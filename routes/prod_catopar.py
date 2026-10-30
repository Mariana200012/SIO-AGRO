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
        
        # 1. Consultamos el historial incluyendo 'pupas', 'estatus' y 'promedio_grandes'
        cursor.execute("""
            SELECT P.id_pre, P.id_lote, P.semana, P.viables, P.chicas, P.medianas, P.grandes, P.pupas, P.promedio_grandes, P.estatus, P.fecha_registro, U.nombre_usuario 
            FROM PRE_PARASITISMO P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            ORDER BY P.id_pre DESC LIMIT 30
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
        
        # 2. Obtener el último registro incluyendo 'estatus' y 'promedio_grandes' para las tarjetas superiores (KPIs)
        cursor.execute("""
            SELECT id_lote, estatus, fecha_registro, promedio_grandes FROM PRE_PARASITISMO ORDER BY id_pre DESC LIMIT 1
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
    total_p = 0
    
    detalles_garbanzos = []
    
    for i in range(1, 22):
        ch = request.form.get(f'g{i}_ch', '0')
        m = request.form.get(f'g{i}_m', '0')
        g = request.form.get(f'g{i}_g', '0')
        p = request.form.get(f'g{i}_p', '0')
        
        ch_val = int(ch) if ch and ch.isdigit() else 0
        m_val = int(m) if m and m.isdigit() else 0
        g_val = int(g) if g and g.isdigit() else 0
        p_val = int(p) if p and p.isdigit() else 0
        
        detalles_garbanzos.append((i, ch_val, m_val, g_val, p_val))

        total_ch += ch_val
        total_m += m_val
        total_g += g_val
        total_p += p_val

    total_viables = total_ch + total_m + total_g
    promedio_grandes = round(total_g / 21.0, 2)
    
    # Todo registro nuevo entra como Pendiente para que el Administrador lo gestione
    estatus_inicial = 'Pendiente'

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
            INSERT INTO PRE_PARASITISMO (id_lote, semana, viables, chicas, medianas, grandes, pupas, promedio_grandes, estatus, id_operador, fecha_registro) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (lote, semana, total_viables, total_ch, total_m, total_g, total_p, promedio_grandes, estatus_inicial, operador['id_usuario'], fecha_final))
        
        id_pre_generado = cursor.lastrowid
        
        # 3. INSERTAR EN EL DETALLE (PRE_PARASITISMO_DETALLE)
        for detalle in detalles_garbanzos:
            num_garbanzo, d_ch, d_m, d_g, d_p = detalle
            if d_ch > 0 or d_m > 0 or d_g > 0 or d_p > 0:
                cursor.execute("""
                    INSERT INTO PRE_PARASITISMO_DETALLE (id_pre, num_garbanzo, chicas, medianas, grandes, pupas) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (id_pre_generado, num_garbanzo, d_ch, d_m, d_g, d_p))

        conn.commit()
        flash(f'Lote {lote} registrado correctamente y enviado a revisión. (Promedio Grandes: {promedio_grandes})', 'success')

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
        
        # 1. Historial con cálculo de porcentaje
        cursor.execute("""
            SELECT C.id_cabecera, C.id_lote, C.semana, C.estatus, C.fecha_registro, U.nombre_usuario,
                   SUM(D.gorg_nacidos) as total_gorg_nacidos,
                   SUM(D.gorg_pupas) as total_gorg_pupas,
                   SUM(D.cat_negros) as total_cat_negros,
                   SUM(D.cat_combinados) as total_cat_combinados,
                   SUM(D.cat_ambar) as total_cat_ambar
            FROM POST_PARASITISMO_CABECERA C
            JOIN USUARIOS U ON C.id_operador = U.id_usuario
            LEFT JOIN POST_PARASITISMO_DETALLE D ON C.id_cabecera = D.id_cabecera
            GROUP BY C.id_cabecera
            ORDER BY C.id_cabecera DESC LIMIT 30
        """)
        filas_historial = cursor.fetchall()
        
        historial = []
        meses_es = {"01":"Ene", "02":"Feb", "03":"Mar", "04":"Abr", "05":"May", "06":"Jun", 
                    "07":"Jul", "08":"Ago", "09":"Sep", "10":"Oct", "11":"Nov", "12":"Dic"}

        for row in filas_historial:
            row_dict = dict(row)
            
            t_gorg = (row_dict.get('total_gorg_nacidos') or 0) + (row_dict.get('total_gorg_pupas') or 0)
            t_cat = (row_dict.get('total_cat_negros') or 0) + (row_dict.get('total_cat_combinados') or 0) + (row_dict.get('total_cat_ambar') or 0)
            total_insectos = t_gorg + t_cat
            porcentaje = (t_cat / total_insectos * 100) if total_insectos > 0 else 0.0
            row_dict['porcentaje'] = round(porcentaje, 1)

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
        
        # 2. Último registro incluyendo el cálculo de porcentaje y hora completa para los KPIs
        cursor.execute("""
            SELECT C.id_cabecera, C.id_lote, C.semana, C.estatus, C.fecha_registro,
                   SUM(D.gorg_nacidos) as total_gorg_nacidos,
                   SUM(D.gorg_pupas) as total_gorg_pupas,
                   SUM(D.cat_negros) as total_cat_negros,
                   SUM(D.cat_combinados) as total_cat_combinados,
                   SUM(D.cat_ambar) as total_cat_ambar
            FROM POST_PARASITISMO_CABECERA C
            LEFT JOIN POST_PARASITISMO_DETALLE D ON C.id_cabecera = D.id_cabecera
            GROUP BY C.id_cabecera
            ORDER BY C.id_cabecera DESC LIMIT 1
        """)
        row_ultimo = cursor.fetchone()
        
        ultimo = None
        if row_ultimo:
            ultimo = dict(row_ultimo)
            
            t_gorg = (ultimo.get('total_gorg_nacidos') or 0) + (ultimo.get('total_gorg_pupas') or 0)
            t_cat = (ultimo.get('total_cat_negros') or 0) + (ultimo.get('total_cat_combinados') or 0) + (ultimo.get('total_cat_ambar') or 0)
            total_insectos = t_gorg + t_cat
            porcentaje = (t_cat / total_insectos * 100) if total_insectos > 0 else 0.0
            ultimo['porcentaje'] = round(porcentaje, 1)

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

        cursor.execute("SELECT id_usuario FROM USUARIOS WHERE nip_firma = ? AND estatus = 'Activo'", (nip,))
        operador = cursor.fetchone()
        if not operador:
            flash('NIP Incorrecto o usuario no activo.', 'error')
            return redirect(url_for('prod_catopar.post'))

        cursor.execute("""
            INSERT INTO POST_PARASITISMO_CABECERA (id_lote, semana, estatus, id_operador, fecha_registro) 
            VALUES (?, ?, 'Pendiente', ?, ?)
        """, (lote, semana, operador['id_usuario'], fecha_final))
        id_cab = cursor.lastrowid

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
    cat_materiales = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        area_actual = session.get('id_area', 2)

        # 1. Obtener historial de solicitudes de Catopar
        cursor.execute(
            """
            SELECT SM.id_solicitud, SM.fecha_solicitud, SM.estatus, U.nombre_usuario, M.nombre_material, SD.cantidad_solicitada
            FROM SOLICITUDES_MATERIAL SM
            JOIN USUARIOS U ON SM.id_operador = U.id_usuario
            JOIN SOLICITUDES_DETALLE SD ON SM.id_solicitud = SD.id_solicitud
            JOIN MATERIALES M ON SD.id_material = M.id_material
            WHERE SM.id_area_solicitante = ?
            ORDER BY SM.id_solicitud DESC
        """,
            (area_actual,),
        )
        filas = cursor.fetchall()

        solicitudes_dict = {}
        for fila in filas:
            id_sol = fila['id_solicitud']
            if id_sol not in solicitudes_dict:
                fecha_formateada = fila['fecha_solicitud']
                if fecha_formateada:
                    try:
                        dt = datetime.strptime(
                            fecha_formateada, '%Y-%m-%d %H:%M:%S'
                        )
                        fecha_formateada = dt.strftime('%d/%m/%Y %I:%M %p')
                    except ValueError:
                        pass

                solicitudes_dict[id_sol] = {
                    'id_solicitud': id_sol,
                    'fecha_solicitud': fecha_formateada,
                    'estatus': fila['estatus'],
                    'nombre_usuario': fila['nombre_usuario'],
                    'materiales': [],
                }
            solicitudes_dict[id_sol]['materiales'].append({
                'nombre_material': fila['nombre_material'],
                'cantidad': fila['cantidad_solicitada'],
            })

        mis_solicitudes = list(solicitudes_dict.values())

        # 2. Obtener lista de materiales registrados para Catopar
        cursor.execute("""
            SELECT M.id_material, M.nombre_material, M.presentacion
            FROM MATERIALES M
            JOIN CAT_AREAS A ON M.id_area = A.id_area
            WHERE A.nombre_area LIKE '%Catopar%'
            ORDER BY M.nombre_material ASC
        """)
        cat_materiales = cursor.fetchall()

        conn.close()
    except Exception as e:
        print('Error al cargar materiales catopar:', e)

    return render_template(
        'produccion/materiales.html',
        origen='catopar',
        mis_solicitudes=mis_solicitudes,
        cat_materiales=cat_materiales,
    )
@prod_catopar_bp.route('/materiales/guardar', methods=['POST'])
def guardar_materiales():
    id_area = session.get('id_area', 2)
    nip_ingresado = request.form.get('nip')
    id_solicitud_editar = request.form.get('id_solicitud_editar')
    fecha_hora_mexico = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Validar NIP del operador
        cursor.execute(
            "SELECT id_usuario, nombre_usuario FROM USUARIOS WHERE nip_firma = ?"
            " AND estatus = 'Activo'",
            (nip_ingresado,),
        )
        operador = cursor.fetchone()

        if not operador:
            flash('NIP incorrecto o usuario no activo.', 'error')
            return redirect(url_for('prod_catopar.materiales'))

        id_operador = operador['id_usuario']

        # 2. Insertar o actualizar la cabecera de la solicitud
        if id_solicitud_editar:
            id_solicitud = id_solicitud_editar
            cursor.execute(
                "UPDATE SOLICITUDES_MATERIAL SET estatus = 'Pendiente',"
                " fecha_solicitud = ? WHERE id_solicitud = ?",
                (fecha_hora_mexico, id_solicitud),
            )
            cursor.execute(
                'DELETE FROM SOLICITUDES_DETALLE WHERE id_solicitud = ?',
                (id_solicitud,),
            )
        else:
            cursor.execute(
                'INSERT INTO SOLICITUDES_MATERIAL (id_operador,'
                ' id_area_solicitante, fecha_solicitud, estatus) VALUES (?, ?,'
                ' ?, ?)',
                (id_operador, id_area, fecha_hora_mexico, 'Pendiente'),
            )
            id_solicitud = cursor.lastrowid

        # 3. Guardar el detalle de materiales seleccionados
        for key, value in request.form.items():
            if key.startswith('material_') and value:
                id_mat = value
                cant = request.form.get(f'cant_{id_mat}', 1)
                cant_val = int(cant) if str(cant).isdigit() and int(cant) > 0 else 1

                cursor.execute(
                    'INSERT INTO SOLICITUDES_DETALLE (id_solicitud,'
                    ' id_material, cantidad_solicitada) VALUES (?, ?, ?)',
                    (id_solicitud, id_mat, cant_val),
                )

        conn.commit()
        flash('Solicitud de materiales enviada correctamente.', 'success')

    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        flash(f'Error al guardar solicitud: {str(e)}', 'error')
    finally:
        if 'conn' in locals() and conn:
            conn.close()

    return redirect(url_for('prod_catopar.materiales'))