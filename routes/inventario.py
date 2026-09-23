import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')

def get_db_connection():
    conn = sqlite3.connect('Bd_SIO-AGRO.db', isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn

# ==========================================
# VISTA DE LA ANALISTA (Ver el Buzón)
# ==========================================
@inventario_bp.route('/solicitudes') 
def listar_solicitudes():
    if session.get('id_area') not in [4, 5]:
        flash('Acceso denegado. Área exclusiva de Inventario.', 'error')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Traemos todas las filas individuales de la base de datos
    cursor.execute("""
        SELECT s.id_solicitud, s.id_operador, s.cantidad_solicitada, s.fecha_solicitud, s.estatus,
               a.nombre_area, u.nombre_usuario, m.nombre_material
        FROM SOLICITUDES_MATERIAL s
        LEFT JOIN CAT_AREAS a ON s.id_area_solicitante = a.id_area
        LEFT JOIN USUARIOS u ON s.id_operador = u.id_usuario
        LEFT JOIN MATERIALES m ON s.id_material = m.id_material
        WHERE s.estatus = 'Pendiente'
        ORDER BY s.fecha_solicitud DESC
    """)
    
    # ¡ESTA ES LA LÍNEA QUE FALTABA!
    filas_bd = cursor.fetchall()
    conn.close()

    # 2. REGLA DE AGRUPACIÓN (Empaquetar filas en Tickets)
    tickets_agrupados = {}
    
    for fila in filas_bd:
        # Creamos la llave cortando la fecha hasta los minutos
        fecha_minuto = fila['fecha_solicitud'][:16]
        llave_ticket = f"{fila['id_operador']}_{fecha_minuto}"
        
        if llave_ticket not in tickets_agrupados:
            tickets_agrupados[llave_ticket] = {
                'folio_ticket': fila['id_solicitud'],
                'nombre_area': fila['nombre_area'],
                'nombre_usuario': fila['nombre_usuario'],
                'fecha_solicitud': fila['fecha_solicitud'],
                'estatus': fila['estatus'],
                'materiales': []
            }
        
        # Agregamos los materiales a la lista interna del ticket
        tickets_agrupados[llave_ticket]['materiales'].append({
            'nombre': fila['nombre_material'],
            'cantidad': fila['cantidad_solicitada']
        })

    # Convertimos el diccionario a una lista para enviarla al HTML
    lista_final_tickets = list(tickets_agrupados.values())

    return render_template('inventario/solicitudes.html', tickets=lista_final_tickets)