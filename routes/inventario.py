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
    try:
        conn = sqlite3.connect(r'C:\Users\maryt\OneDrive\Escritorio\Proyecto\SF_Koppert\Bd_SIO-AGRO.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Consulta uniendo Cabecera y Detalle, filtrando solo los activos
        cursor.execute("""
            SELECT 
                SM.id_solicitud, 
                SM.fecha_solicitud, 
                SM.estatus, 
                U.nombre_usuario,
                A.nombre_area,
                M.nombre_material,
                SD.cantidad_solicitada
            FROM SOLICITUDES_MATERIAL SM
            JOIN USUARIOS U ON SM.id_operador = U.id_usuario
            JOIN CAT_AREAS A ON SM.id_area_solicitante = A.id_area
            JOIN SOLICITUDES_DETALLE SD ON SM.id_solicitud = SD.id_solicitud
            JOIN MATERIALES M ON SD.id_material = M.id_material
            WHERE SM.estatus IN ('Pendiente', 'Autorizado')
            ORDER BY SM.id_solicitud DESC
        """)
        
        filas = cursor.fetchall()
        
        # Agrupamos los materiales por Folio para la vista del analista
        tickets_dict = {}
        for fila in filas:
            folio = fila['id_solicitud']
            if folio not in tickets_dict:
                tickets_dict[folio] = {
                    'folio_ticket': folio,
                    'fecha_solicitud': fila['fecha_solicitud'],
                    'estatus': fila['estatus'],
                    'nombre_usuario': fila['nombre_usuario'],
                    'nombre_area': fila['nombre_area'],
                    'materiales': []
                }
            # Insertamos los materiales dentro del ticket correspondiente
            tickets_dict[folio]['materiales'].append({
                'nombre': fila['nombre_material'],
                'cantidad': fila['cantidad_solicitada']
            })
            
        tickets = list(tickets_dict.values())
        conn.close()

    except Exception as e:
        print(f"Error en inventario: {e}")
        tickets = []

    return render_template('inventario/solicitudes.html', tickets=tickets)

@inventario_bp.route('/historial')
def historial_solicitudes():
    try:
        conn = sqlite3.connect(r'C:\Users\maryt\OneDrive\Escritorio\Proyecto\SF_Koppert\Bd_SIO-AGRO.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Usamos la misma estructura de JOIN, pero filtramos por Surtido, Completado o Rechazado
        cursor.execute("""
            SELECT 
                SM.id_solicitud, 
                SM.fecha_solicitud, 
                SM.estatus, 
                U.nombre_usuario,
                A.nombre_area,
                M.nombre_material,
                SD.cantidad_solicitada
            FROM SOLICITUDES_MATERIAL SM
            JOIN USUARIOS U ON SM.id_operador = U.id_usuario
            JOIN CAT_AREAS A ON SM.id_area_solicitante = A.id_area
            JOIN SOLICITUDES_DETALLE SD ON SM.id_solicitud = SD.id_solicitud
            JOIN MATERIALES M ON SD.id_material = M.id_material
            WHERE SM.estatus IN ('Surtido', 'Completado', 'Rechazado')
            ORDER BY SM.id_solicitud DESC
        """)
        
        filas = cursor.fetchall()
        
        # Agrupamos los materiales por Folio para el historial
        tickets_dict = {}
        for fila in filas:
            folio = fila['id_solicitud']
            if folio not in tickets_dict:
                tickets_dict[folio] = {
                    'folio_ticket': folio,
                    'fecha_solicitud': fila['fecha_solicitud'],
                    'estatus': fila['estatus'],
                    'nombre_usuario': fila['nombre_usuario'],
                    'nombre_area': fila['nombre_area'],
                    'materiales': []
                }
            tickets_dict[folio]['materiales'].append({
                'nombre': fila['nombre_material'],
                'cantidad': fila['cantidad_solicitada']
            })
            
        tickets_historial = list(tickets_dict.values())
        conn.close()

    except Exception as e:
        print(f"Error en historial inventario: {e}")
        tickets_historial = []

    return render_template('inventario/historial.html', tickets_historial=tickets_historial)



# ==========================================
# PROCESAR BOTONES DE ACCIÓN (Autorizar/Surtir)
# ==========================================
# ==========================================
# PROCESAR BOTONES DE ACCIÓN (Autorizar/Surtir)
# ==========================================
@inventario_bp.route('/solicitudes/actualizar/<int:folio>', methods=['POST'])
def actualizar_ticket(folio):
    # Saber qué botón presionó el usuario
    accion = request.form.get('accion')
    
    # Determinar el nuevo estado
    nuevo_estatus = ''
    if accion == 'autorizar':
        nuevo_estatus = 'Autorizado'
    elif accion == 'surtir':
        nuevo_estatus = 'Completado'
    elif accion == 'rechazar':
        nuevo_estatus = 'Rechazado'

    if nuevo_estatus:
        try:
            # Usamos tu misma función de conexión
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Actualizamos ÚNICAMENTE el ticket exacto que el usuario presionó
            cursor.execute("""
                UPDATE SOLICITUDES_MATERIAL 
                SET estatus = ? 
                WHERE id_solicitud = ?
            """, (nuevo_estatus, folio))
            
            conn.commit()
            flash(f'El ticket #REQ-00{folio} fue marcado como: {nuevo_estatus}.', 'success')
                
        except Exception as e:
            flash(f'Ocurrió un error al actualizar la base de datos: {e}', 'error')
        finally:
            if 'conn' in locals():
                conn.close()

    # Redirigir de vuelta a la vista de solicitudes
    return redirect(url_for('inventario.listar_solicitudes'))