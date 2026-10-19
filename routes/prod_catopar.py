from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import sqlite3

prod_catopar_bp = Blueprint('prod_catopar', __name__, url_prefix='/piso/catopar')

def get_db_connection():
    conn = sqlite3.connect('Bd_SIO-AGRO.db', isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn

# =====================================================================
# 1. MÓDULO PRE-PARASITISMO
# =====================================================================
@prod_catopar_bp.route('/pre')
def pre():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Consultamos el historial incluyendo 'estatus'
        cursor.execute("""
            SELECT P.id_pre, P.id_lote, P.semana, P.viables, P.chicas, P.medianas, P.grandes, P.estatus, P.fecha_registro, U.nombre_usuario 
            FROM PRE_PARASITISMO P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            ORDER BY P.id_pre DESC LIMIT 15
        """)
        filas_historial = cursor.fetchall()
        
        historial = []
        meses_es = {"01":"Ene", "02":"Feb", "03":"Mar", "04":"Abr", "05":"May", "06":"Jun", 
                    "07":"Jul", "08":"Ago", "09":"Sep", "10":"Oct", "11":"Nov", "12":"Dic"}

        for row in filas_historial:
            row_dict = dict(row)
            
            # Formatear la fecha a 12 horas con mes en letra
            if row_dict['fecha_registro']:
                try:
                    fecha_obj = datetime.strptime(row_dict['fecha_registro'][:10], '%Y-%m-%d')
                    dia = fecha_obj.strftime('%d')
                    mes_num = fecha_obj.strftime('%m')
                    anio = fecha_obj.strftime('%Y')
                    
                    hora_str = ""
                    if len(row_dict['fecha_registro']) > 10:
                        hora_obj = datetime.strptime(row_dict['fecha_registro'], '%Y-%m-%d %H:%M:%S')
                        hora_str = hora_obj.strftime(' %I:%M %p')
                    
                    row_dict['fecha_registro'] = f"{dia}-{meses_es[mes_num]}-{anio}{hora_str}"
                except ValueError:
                    pass
            
            historial.append(row_dict)
        
        # 2. Obtener el último registro incluyendo 'estatus' para las tarjetas superiores (KPIs)
        cursor.execute("""
            SELECT id_lote, estatus, fecha_registro FROM PRE_PARASITISMO ORDER BY id_pre DESC LIMIT 1
        """)
        row_ultimo = cursor.fetchone()
        
        ultimo = None
        if row_ultimo:
            ultimo = dict(row_ultimo)
            if ultimo['fecha_registro']:
                try:
                    fecha_obj = datetime.strptime(ultimo['fecha_registro'][:10], '%Y-%m-%d')
                    dia = fecha_obj.strftime('%d')
                    mes_num = fecha_obj.strftime('%m')
                    anio = fecha_obj.strftime('%Y')
                    
                    hora_str = ""
                    if len(row_ultimo['fecha_registro']) > 10:
                        hora_obj = datetime.strptime(row_ultimo['fecha_registro'], '%Y-%m-%d %H:%M:%S')
                        hora_str = hora_obj.strftime(' %I:%M %p')

                    ultimo['fecha_registro'] = f"{dia}-{meses_es[mes_num]}-{anio}{hora_str}"
                except ValueError:
                    pass

        conn.close()
    except Exception as e:
        print("Error en Pre-Parasitismo:", e)
        historial = []
        ultimo = None
        
    return render_template('produccion/catopar/pre.html', historial=historial, ultimo=ultimo)

@prod_catopar_bp.route('/pre/guardar', methods=['POST'])
def guardar_pre():
    lote = request.form.get('lote_id')
    semana = request.form.get('semana')
    fecha_input = request.form.get('fecha')
    nip = request.form.get('nip')
    
    hora_actual = datetime.now().strftime('%H:%M:%S')
    fecha_final = f"{fecha_input} {hora_actual}"

    total_ch = 0
    total_m = 0
    total_g = 0
    
    # Validamos y sumamos los 21 garbanzos antes de tocar la base de datos
    detalles_garbanzos = []
    
    for i in range(1, 22):
        ch = request.form.get(f'g{i}_ch', '0')
        m = request.form.get(f'g{i}_m', '0')
        g = request.form.get(f'g{i}_g', '0')
        
        ch_val = int(ch) if ch and ch.isdigit() else 0
        m_val = int(m) if m and m.isdigit() else 0
        g_val = int(g) if g and g.isdigit() else 0
        
        # Guardamos temporalmente en una lista para insertarlos después
        detalles_garbanzos.append((i, ch_val, m_val, g_val))

        total_ch += ch_val
        total_m += m_val
        total_g += g_val

    total_viables = total_ch + total_m + total_g

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Validar firma NIP
        cursor.execute("SELECT id_usuario FROM USUARIOS WHERE nip_firma = ? AND estatus = 'Activo'", (nip,))
        operador = cursor.fetchone()
        
        if not operador:
            flash('NIP Incorrecto o usuario no activo.', 'error')
            return redirect(url_for('prod_catopar.pre'))

        # 2. INSERTAR EN LA CABECERA (PRE_PARASITISMO)
        cursor.execute("""
            INSERT INTO PRE_PARASITISMO (id_lote, semana, viables, chicas, medianas, grandes, estatus, id_operador, fecha_registro) 
            VALUES (?, ?, ?, ?, ?, ?, 'Pendiente', ?, ?)
        """, (lote, semana, total_viables, total_ch, total_m, total_g, operador['id_usuario'], fecha_final))
        
        # Obtenemos el ID del registro de cabecera que acabamos de crear
        id_pre_generado = cursor.lastrowid
        
        # 3. INSERTAR EN EL DETALLE (PRE_PARASITISMO_DETALLE)
        for detalle in detalles_garbanzos:
            num_garbanzo, d_ch, d_m, d_g = detalle
            if d_ch > 0 or d_m > 0 or d_g > 0:
                cursor.execute("""
                    INSERT INTO PRE_PARASITISMO_DETALLE (id_pre, num_garbanzo, chicas, medianas, grandes) 
                    VALUES (?, ?, ?, ?, ?)
                """, (id_pre_generado, num_garbanzo, d_ch, d_m, d_g))

        # Confirmamos toda la transacción
        conn.commit()
        flash(f'Muestra {lote} registrada correctamente. (CH:{total_ch}, M:{total_m}, G:{total_g})', 'success')

    except Exception as e:
        flash(f'Error al guardar en base de datos: {str(e)}', 'error')
    finally:
        if 'conn' in locals(): conn.close()

    return redirect(url_for('prod_catopar.pre'))

# =====================================================================
# 2. MÓDULO POST-PARASITISMO (CON VOZ)
# =====================================================================
@prod_catopar_bp.route('/post')
def post():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # CAMBIO AQUÍ: Usamos SUM(D.gorg_nacidos) y SUM(D.gorg_pupas) que son los nombres reales en tu BD
        cursor.execute("""
            SELECT C.id_cabecera, C.id_lote, C.semana, C.estatus, C.fecha_registro, U.nombre_usuario,
                   SUM(D.gorg_nacidos) as total_acaros, SUM(D.gorg_pupas) as total_completos
            FROM POST_PARASITISMO_CABECERA C
            JOIN USUARIOS U ON C.id_operador = U.id_usuario
            LEFT JOIN POST_PARASITISMO_DETALLE D ON C.id_cabecera = D.id_cabecera
            GROUP BY C.id_cabecera
            ORDER BY C.id_cabecera DESC LIMIT 15
        """)
        filas_historial = cursor.fetchall()
        
        historial = []
        meses_es = {"01":"Ene", "02":"Feb", "03":"Mar", "04":"Abr", "05":"May", "06":"Jun", 
                    "07":"Jul", "08":"Ago", "09":"Sep", "10":"Oct", "11":"Nov", "12":"Dic"}

        for row in filas_historial:
            row_dict = dict(row)
            if row_dict['fecha_registro']:
                try:
                    fecha_obj = datetime.strptime(row_dict['fecha_registro'][:10], '%Y-%m-%d')
                    dia = fecha_obj.strftime('%d')
                    mes_num = fecha_obj.strftime('%m')
                    anio = fecha_obj.strftime('%Y')
                    
                    hora_str = ""
                    if len(row_dict['fecha_registro']) > 10:
                        hora_obj = datetime.strptime(row_dict['fecha_registro'], '%Y-%m-%d %H:%M:%S')
                        hora_str = hora_obj.strftime(' %I:%M %p')
                    
                    row_dict['fecha_registro'] = f"{dia}-{meses_es[mes_num]}-{anio}{hora_str}"
                except ValueError:
                    pass
            historial.append(row_dict)
        
        # 2. Obtener el último registro para los KPIs superiores
        cursor.execute("""
            SELECT id_lote, estatus, fecha_registro FROM POST_PARASITISMO_CABECERA ORDER BY id_cabecera DESC LIMIT 1
        """)
        row_ultimo = cursor.fetchone()
        ultimo = dict(row_ultimo) if row_ultimo else None
        
        if ultimo and ultimo['fecha_registro']:
            try:
                fecha_obj = datetime.strptime(ultimo['fecha_registro'][:10], '%Y-%m-%d')
                ultimo['fecha_registro'] = f"{fecha_obj.strftime('%d')}-{meses_es[fecha_obj.strftime('%m')]}-{fecha_obj.strftime('%Y')}"
            except ValueError:
                pass

        conn.close()
    except Exception as e:
        print("Error en Post-Parasitismo:", e)
        historial = []
        ultimo = None
        
    return render_template('produccion/catopar/post.html', historial=historial, ultimo=ultimo)

@prod_catopar_bp.route('/post/guardar', methods=['POST'])
def guardar_post():
    lote = request.form.get('lote_id')
    semana = request.form.get('semana')
    fecha_input = request.form.get('fecha')
    nip = request.form.get('nip')
    
    hora_actual = datetime.now().strftime('%H:%M:%S')
    fecha_final = f"{fecha_input} {hora_actual}"

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Validar NIP
        cursor.execute("SELECT id_usuario FROM USUARIOS WHERE nip_firma = ? AND estatus = 'Activo'", (nip,))
        operador = cursor.fetchone()
        if not operador:
            flash('NIP Incorrecto o usuario no activo.', 'error')
            return redirect(url_for('prod_catopar.post'))

        # 2. Insertar en CABECERA
        cursor.execute("""
            INSERT INTO POST_PARASITISMO_CABECERA (id_lote, semana, estatus, id_operador, fecha_registro) 
            VALUES (?, ?, 'Pendiente', ?, ?)
        """, (lote, semana, operador['id_usuario'], fecha_final))
        id_cab = cursor.lastrowid

        # 3. Extraer e insertar DETALLE (Las 10 filas del HTML)
        total_acaros = 0
        total_completos = 0
        
        for i in range(1, 11):
            acaros = int(request.form.get(f'acaros_{i}', 0) or 0)
            completos = int(request.form.get(f'completos_{i}', 0) or 0)
            negro = int(request.form.get(f'negro_{i}', 0) or 0)
            combinado = int(request.form.get(f'combinado_{i}', 0) or 0)
            ambar = int(request.form.get(f'ambar_{i}', 0) or 0)
            
            total_acaros += acaros
            total_completos += completos

            if acaros > 0 or completos > 0 or negro > 0 or combinado > 0 or ambar > 0:
                # CAMBIO AQUÍ: Cambiamos 'num_garbanzo' por 'numero_garbanzo' y los nombres exactos que tenías originalmente
                cursor.execute("""
                    INSERT INTO POST_PARASITISMO_DETALLE 
                    (id_cabecera, numero_garbanzo, gorg_nacidos, gorg_pupas, cat_negros, cat_combinados, cat_ambar) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (id_cab, i, acaros, completos, negro, combinado, ambar))

        conn.commit()
        flash(f'Lote {lote} registrado exitosamente. (Ácaros: {total_acaros}, Completos: {total_completos})', 'success')
        
    except Exception as e:
        flash(f'Error al guardar en base de datos: {str(e)}', 'error')
    finally:
        if 'conn' in locals(): conn.close()

    return redirect(url_for('prod_catopar.post'))

# =====================================================================
# 3. MÓDULO MATERIALES (Exclusivo para Catopar)
# =====================================================================
@prod_catopar_bp.route('/materiales')
def materiales():
    mis_solicitudes = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # CORREGIDO: Filtramos por el id_area de Catopar (2) o dinámicamente por la sesión
        area_actual = session.get('id_area', 2)
        
        cursor.execute("""
            SELECT SM.id_solicitud, SM.fecha_solicitud, SM.estatus, U.nombre_usuario, M.nombre_material, SD.cantidad_solicitada
            FROM SOLICITUDES_MATERIAL SM
            JOIN USUARIOS U ON SM.id_operador = U.id_usuario
            JOIN SOLICITUDES_DETALLE SD ON SM.id_solicitud = SD.id_solicitud
            JOIN MATERIALES M ON SD.id_material = M.id_material
            WHERE SM.id_area_solicitante = ?
            ORDER BY SM.id_solicitud DESC
        """, (area_actual,))
        filas = cursor.fetchall()
        
        solicitudes_dict = {}
        for fila in filas:
            id_sol = fila['id_solicitud']
            if id_sol not in solicitudes_dict:
                # Convertir fecha de la solicitud a formato de 12 horas si existe
                fecha_formateada = fila['fecha_solicitud']
                if fecha_formateada:
                    try:
                        dt = datetime.strptime(fecha_formateada, '%Y-%m-%d %H:%M:%S')
                        fecha_formateada = dt.strftime('%d/%m/%Y %I:%M %p')
                    except ValueError:
                        pass

                solicitudes_dict[id_sol] = {
                    'id_solicitud': id_sol, 'fecha_solicitud': fecha_formateada,
                    'estatus': fila['estatus'], 'nombre_usuario': fila['nombre_usuario'],
                    'materiales': []
                }
            solicitudes_dict[id_sol]['materiales'].append({
                'nombre_material': fila['nombre_material'], 'cantidad': fila['cantidad_solicitada']
            })
            
        mis_solicitudes = list(solicitudes_dict.values())
        conn.close()
    except Exception as e:
        print("Error al cargar materiales catopar:", e)

    return render_template('produccion/materiales.html', origen='catopar', mis_solicitudes=mis_solicitudes)

@prod_catopar_bp.route('/materiales/guardar', methods=['POST'])
def guardar_materiales():
    # CORREGIDO: Aseguramos que tome el área de la sesión o por defecto Catopar (2)
    id_area = session.get('id_area', 2)  
    nip_ingresado = request.form.get('nip')
    id_solicitud_editar = request.form.get('id_solicitud_editar')
    fecha_hora_mexico = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id_usuario, nombre_usuario FROM USUARIOS WHERE nip_firma = ? AND estatus = 'Activo'", (nip_ingresado,))
        operador = cursor.fetchone()
        
        if not operador:
            flash('NIP Incorrecto o usuario no activo.', 'error')
            return redirect(url_for('prod_catopar.materiales'))
            
        materiales_pedidos = []
        for i in range(1, 20):
            if request.form.get(f'material_{i}'):
                cantidad = request.form.get(f'cant_{i}')
                if cantidad and int(cantidad) > 0:
                    materiales_pedidos.append({'id_material': i, 'cantidad': int(cantidad)})
                    
        if not materiales_pedidos:
            flash('Debes seleccionar al menos un material.', 'error')
            return redirect(url_for('prod_catopar.materiales'))

        if id_solicitud_editar:
            cursor.execute("UPDATE SOLICITUDES_MATERIAL SET estatus = 'Pendiente', fecha_solicitud = ?, id_operador = ? WHERE id_solicitud = ?", (fecha_hora_mexico, operador['id_usuario'], id_solicitud_editar))
            cursor.execute("DELETE FROM SOLICITUDES_DETALLE WHERE id_solicitud = ?", (id_solicitud_editar,))
            for mat in materiales_pedidos:
                cursor.execute("INSERT INTO SOLICITUDES_DETALLE (id_solicitud, id_material, cantidad_solicitada) VALUES (?, ?, ?)", (id_solicitud_editar, mat['id_material'], mat['cantidad']))
            flash(f'Solicitud corregida por {operador["nombre_usuario"]}.', 'success')
        else:
            cursor.execute("INSERT INTO SOLICITUDES_MATERIAL (id_area_solicitante, id_operador, estatus, fecha_solicitud) VALUES (?, ?, 'Pendiente', ?)", (id_area, operador['id_usuario'], fecha_hora_mexico))
            nuevo_folio = cursor.lastrowid
            for mat in materiales_pedidos:
                cursor.execute("INSERT INTO SOLICITUDES_DETALLE (id_solicitud, id_material, cantidad_solicitada) VALUES (?, ?, ?)", (nuevo_folio, mat['id_material'], mat['cantidad']))
            flash(f'Solicitud enviada por {operador["nombre_usuario"]}.', 'success')
            
        conn.commit()
    except Exception as e:
        if 'conn' in locals() and conn: conn.rollback()
        flash(f'Error al guardar solicitud: {str(e)}', 'error')
    finally:
        if 'conn' in locals() and conn: conn.close()
        
    return redirect(url_for('prod_catopar.materiales'))