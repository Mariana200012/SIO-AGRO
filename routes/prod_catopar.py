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
        
        # Historial de tabla
        cursor.execute("""
            SELECT P.id_lote, P.viables, P.fecha_registro, U.nombre_usuario 
            FROM PRE_PARASITISMO P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            ORDER BY P.id_pre DESC LIMIT 15
        """)
        filas_historial = cursor.fetchall()
        
        # Formatear la fecha a 12 horas (AM/PM) en cada registro del historial
        historial = []
        for row in filas_historial:
            row_dict = dict(row)
            if row_dict['fecha_registro']:
                try:
                    dt = datetime.strptime(row_dict['fecha_registro'], '%Y-%m-%d %H:%M:%S')
                    row_dict['fecha_registro'] = dt.strftime('%d/%m/%Y %I:%M %p')
                except ValueError:
                    pass
            historial.append(row_dict)
        
        # Último registro para la tarjeta resumen
        cursor.execute("SELECT id_lote, viables, fecha_registro FROM PRE_PARASITISMO ORDER BY id_pre DESC LIMIT 1")
        row_ultimo = cursor.fetchone()
        
        ultimo = None
        if row_ultimo:
            ultimo = dict(row_ultimo)
            if ultimo['fecha_registro']:
                try:
                    dt = datetime.strptime(ultimo['fecha_registro'], '%Y-%m-%d %H:%M:%S')
                    ultimo['fecha_registro'] = dt.strftime('%d/%m/%Y %I:%M %p')
                except ValueError:
                    pass

        conn.close()
    except Exception as e:
        print("Error en Pre-Parasitismo:", e)
        historial = []; ultimo = None
        
    return render_template('produccion/catopar/pre.html', historial=historial, ultimo=ultimo)

@prod_catopar_bp.route('/pre/guardar', methods=['POST'])
def guardar_pre():
    lote = request.form.get('lote_id')
    viables = int(request.form.get('viables'))
    nip = request.form.get('nip')
    # Guardar internamente en formato estándar de BD (24h para ordenamiento correcto)
    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Validar firma NIP
        cursor.execute("SELECT id_usuario FROM USUARIOS WHERE nip_firma = ? AND estatus = 'Activo'", (nip,))
        operador = cursor.fetchone()
        
        if not operador:
            flash('NIP Incorrecto o usuario no activo.', 'error')
            return redirect(url_for('prod_catopar.pre'))

        # Guardar en tabla PRE_PARASITISMO
        cursor.execute("INSERT INTO PRE_PARASITISMO (id_lote, viables, id_operador, fecha_registro) VALUES (?, ?, ?, ?)", 
                       (lote, viables, operador['id_usuario'], fecha_actual))
        
        conn.commit()
        flash(f'Muestra {lote} registrada correctamente.', 'success')

    except Exception as e:
        flash(f'Error al guardar: {str(e)}', 'error')
    finally:
        if 'conn' in locals(): conn.close()

    return redirect(url_for('prod_catopar.pre'))


# =====================================================================
# 2. MÓDULO POST-PARASITISMO (CON VOZ)
# =====================================================================
@prod_catopar_bp.route('/post')
def post():
    return render_template('produccion/catopar/post.html')

@prod_catopar_bp.route('/post/guardar', methods=['POST'])
def guardar_post():
    datos = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Validar NIP
        cursor.execute("SELECT id_usuario FROM USUARIOS WHERE nip_firma = ? AND estatus = 'Activo'", (datos.get('nip'),))
        operador = cursor.fetchone()
        if not operador:
            return jsonify({'status': 'error', 'message': 'NIP Incorrecto o usuario inactivo.'}), 403

        # Insertar CABECERA (Formato estándar para BD)
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO POST_PARASITISMO_CABECERA (id_lote, id_operador, fecha_registro) VALUES (?, ?, ?)",
                       (datos.get('lote'), operador['id_usuario'], fecha_actual))
        id_cab = cursor.lastrowid

        # Insertar DETALLE (Los 10 garbanzos)
        garbanzos = datos.get('garbanzos', [])
        for g in garbanzos:
            cursor.execute("""
                INSERT INTO POST_PARASITISMO_DETALLE 
                (id_cabecera, numero_garbanzo, gorg_nacidos, gorg_pupas, cat_negros, cat_combinados, cat_ambar) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (id_cab, g['numero'], g['g_nac'], g['g_pup'], g['c_neg'], g['c_com'], g['c_amb']))

        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# =====================================================================
# 3. MÓDULO MATERIALES (Exclusivo para Catopar)
# =====================================================================
@prod_catopar_bp.route('/materiales')
def materiales():
    mis_solicitudes = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT SM.id_solicitud, SM.fecha_solicitud, SM.estatus, U.nombre_usuario, M.nombre_material, SD.cantidad_solicitada
            FROM SOLICITUDES_MATERIAL SM
            JOIN USUARIOS U ON SM.id_operador = U.id_usuario
            JOIN SOLICITUDES_DETALLE SD ON SM.id_solicitud = SD.id_solicitud
            JOIN MATERIALES M ON SD.id_material = M.id_material
            WHERE SM.id_area_solicitante = 5
            ORDER BY SM.id_solicitud DESC
        """)
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
    id_area = session.get('id_area', 5)  # ID 5 suele ser Catopar
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