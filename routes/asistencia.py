from flask import Blueprint, render_template, jsonify, session, flash, redirect, url_for
from datetime import datetime
import sqlite3

asistencia_bp = Blueprint('asistencia', __name__, url_prefix='/asistencia')

def get_db_connection():
    # Usamos tu ruta completa para evitar el error de "no such table"
    conn = sqlite3.connect(r'C:\Users\maryt\OneDrive\Escritorio\Proyecto\SF_Koppert\Bd_SIO-AGRO.db')
    conn.row_factory = sqlite3.Row
    return conn

# RUTA 1: Muestra la pantalla solo con los operadores del área del encargado
@asistencia_bp.route('/pase_lista')
def pase_lista():
    # 1. Obtenemos el área del encargado que inició sesión
    id_area_encargado = session.get('id_area')
    
    if not id_area_encargado:
        flash("Error: Sesión no válida o área no asignada.", "error")
        return redirect(url_for('auth.login'))

    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 2. EL FILTRO MÁGICO: Misma área del encargado Y puesto 'Operador'
    cursor.execute("""
        SELECT U.id_usuario, U.nombre_usuario, 
               A.id_asistencia, A.hora_entrada
        FROM USUARIOS U
        LEFT JOIN ASISTENCIA A ON U.id_usuario = A.id_usuario AND A.fecha = ?
        WHERE U.id_area = ? AND U.estatus = 'Activo' AND U.puesto = 'Operador'
        ORDER BY U.nombre_usuario
    """, (fecha_hoy, id_area_encargado))
    
    filas_operadores = cursor.fetchall()
    conn.close()
    
    # Formatear la hora de entrada a 12 horas (AM/PM) para que se vea bien en el HTML
    operadores = []
    for op in filas_operadores:
        op_dict = dict(op)
        if op_dict['hora_entrada']:
            try:
                # Intenta parsear la hora (soporta formato HH:MM:SS o HH:MM)
                for fmt in ('%H:%M:%S', '%H:%M'):
                    try:
                        dt = datetime.strptime(op_dict['hora_entrada'], fmt)
                        op_dict['hora_entrada'] = dt.strftime('%I:%M %p')
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
        operadores.append(op_dict)
    
    return render_template('produccion/prod_asistencia.html', operadores=operadores)

# RUTA 2: Guarda ÚNICAMENTE la entrada
@asistencia_bp.route('/marcar/<int:id_operador>', methods=['POST'])
def marcar_asistencia(id_operador):
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    hora_actual_bd = datetime.now().strftime('%H:%M:%S') # Formato 24h para almacenar en BD
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Revisamos si ya tiene entrada
        cursor.execute("SELECT id_asistencia FROM ASISTENCIA WHERE id_usuario = ? AND fecha = ?", (id_operador, fecha_hoy))
        registro = cursor.fetchone()
        
        if not registro:
            # Solo si no existe, insertamos la Entrada
            cursor.execute("INSERT INTO ASISTENCIA (id_usuario, fecha, hora_entrada, estatus) VALUES (?, ?, ?, 'En turno')", (id_operador, fecha_hoy, hora_actual_bd))
            estado = 'entrada'
        else:
            estado = 'completado' # Ya se había marcado antes
            
        conn.commit()
        conn.close()
        
        # Convertir la hora actual a formato de 12 horas con AM/PM para la respuesta JSON
        hora_bonita = datetime.now().strftime('%I:%M %p')
        
        return jsonify({'status': 'success', 'estado': estado, 'hora': hora_bonita})
    except Exception as e:
        print(f"Error al marcar asistencia: {e}")
        return jsonify({'status': 'error'})