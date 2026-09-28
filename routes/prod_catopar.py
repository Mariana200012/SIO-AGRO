import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime

prod_catopar_bp = Blueprint('prod_catopar', __name__, url_prefix='/piso/catopar')

def get_db_connection():
    conn = sqlite3.connect(r'C:\Users\maryt\OneDrive\Escritorio\Proyecto\SF_Koppert\Bd_SIO-AGRO.db')
    conn.row_factory = sqlite3.Row
    return conn

# ==========================================
# RUTAS DE PRODUCCIÓN
# ==========================================
@prod_catopar_bp.route('/pre', methods=['GET'])
def pre():
    return render_template('produccion/catopar/pre.html')

@prod_catopar_bp.route('/post', methods=['GET'])
def post():
    return render_template('produccion/catopar/post.html')

# ==========================================
# RUTAS DE MATERIALES (Ya con la hora corregida)
# ==========================================
@prod_catopar_bp.route('/materiales')
def materiales():
    id_operador = session.get('id_usuario')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consulta uniendo la Cabecera con el Detalle
        cursor.execute("""
            SELECT 
                SM.id_solicitud, 
                SM.fecha_solicitud, 
                SM.estatus, 
                U.nombre_usuario,
                M.nombre_material,
                SD.cantidad_solicitada
            FROM SOLICITUDES_MATERIAL SM
            JOIN USUARIOS U ON SM.id_operador = U.id_usuario
            JOIN SOLICITUDES_DETALLE SD ON SM.id_solicitud = SD.id_solicitud
            JOIN MATERIALES M ON SD.id_material = M.id_material
            WHERE SM.id_operador = ?
            ORDER BY SM.id_solicitud DESC
        """, (id_operador,))
        
        filas = cursor.fetchall()
        
        # Agrupamos los materiales por Folio para mandarlos a Jinja2
        solicitudes_dict = {}
        for fila in filas:
            id_sol = fila['id_solicitud']
            if id_sol not in solicitudes_dict:
                solicitudes_dict[id_sol] = {
                    'id_solicitud': id_sol,
                    'fecha_solicitud': fila['fecha_solicitud'],
                    'estatus': fila['estatus'],
                    'nombre_usuario': fila['nombre_usuario'],
                    'materiales': []
                }
            solicitudes_dict[id_sol]['materiales'].append({
                'nombre_material': fila['nombre_material'],
                'cantidad': fila['cantidad_solicitada']
            })
            
        mis_solicitudes = list(solicitudes_dict.values())
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        mis_solicitudes = []

    return render_template('produccion/materiales.html', origen='catopar', mis_solicitudes=mis_solicitudes)


@prod_catopar_bp.route('/materiales/guardar', methods=['POST'])
def guardar_materiales():
    id_operador = session.get('id_usuario')
    id_area = session.get('id_area')
    nip = request.form.get('nip')
    id_solicitud_editar = request.form.get('id_solicitud_editar') 
    
    # 🌟 LA HORA CORRECTA INYECTADA MANUALMENTE
    fecha_hora_mexico = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    materiales_pedidos = []
    for i in range(1, 15):
        if request.form.get(f'material_{i}'):
            cantidad = request.form.get(f'cant_{i}')
            if cantidad and int(cantidad) > 0:
                materiales_pedidos.append({
                    'id_material': i, 
                    'cantidad': int(cantidad)
                })

    if not materiales_pedidos:
        flash('Debes seleccionar al menos un material e indicar la cantidad.', 'error')
        return redirect(url_for('prod_catopar.materiales'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if id_solicitud_editar:
            # MODO EDICIÓN
            cursor.execute("""
                UPDATE SOLICITUDES_MATERIAL 
                SET estatus = 'Pendiente', fecha_solicitud = ?
                WHERE id_solicitud = ?
            """, (fecha_hora_mexico, id_solicitud_editar))

            cursor.execute("DELETE FROM SOLICITUDES_DETALLE WHERE id_solicitud = ?", (id_solicitud_editar,))

            for mat in materiales_pedidos:
                cursor.execute("""
                    INSERT INTO SOLICITUDES_DETALLE (id_solicitud, id_material, cantidad_solicitada)
                    VALUES (?, ?, ?)
                """, (id_solicitud_editar, mat['id_material'], mat['cantidad']))
                
            flash(f'Solicitud #SOL-00{id_solicitud_editar} corregida y enviada a revisión nuevamente.', 'success')

        else:
            # MODO NUEVO PEDIDO
            cursor.execute("""
                INSERT INTO SOLICITUDES_MATERIAL (id_area_solicitante, id_operador, estatus, fecha_solicitud)
                VALUES (?, ?, 'Pendiente', ?)
            """, (id_area, id_operador, fecha_hora_mexico))
            
            nuevo_folio = cursor.lastrowid

            for mat in materiales_pedidos:
                cursor.execute("""
                    INSERT INTO SOLICITUDES_DETALLE (id_solicitud, id_material, cantidad_solicitada)
                    VALUES (?, ?, ?)
                """, (nuevo_folio, mat['id_material'], mat['cantidad']))

            flash('Nueva solicitud de materiales enviada al almacén correctamente.', 'success')

        conn.commit()

    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        flash(f'Error de base de datos: {str(e)}', 'error')
    finally:
        if 'conn' in locals() and conn:
            conn.close()

    return redirect(url_for('prod_catopar.materiales'))


@prod_catopar_bp.route('/materiales/detalle/<int:id_solicitud>')
def detalle_solicitud(id_solicitud):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id_material, cantidad_solicitada 
            FROM SOLICITUDES_DETALLE 
            WHERE id_solicitud = ?
        """, (id_solicitud,))
        
        filas = cursor.fetchall()
        datos = [{"id_material": f["id_material"], "cantidad": f["cantidad_solicitada"]} for f in filas]
        
        conn.close()
        return jsonify(datos)

    except Exception as e:
        return jsonify({"error": str(e)}), 500