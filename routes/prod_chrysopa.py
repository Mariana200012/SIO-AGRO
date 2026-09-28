from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import sqlite3

prod_chrysopa_bp = Blueprint('prod_chrysopa', __name__, url_prefix='/piso/chrysopa')

def get_db_connection():
    conn = sqlite3.connect('Bd_SIO-AGRO.db', isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn

@prod_chrysopa_bp.route('/validar_nip_ajax', methods=['POST'])
def validar_nip_ajax():
    nip = request.json.get('nip')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre_usuario FROM USUARIOS WHERE nip_firma = ? AND estatus = 'Activo'", (nip,))
        user = cursor.fetchone()
        conn.close()
        if user:
            return jsonify({'status': 'success', 'nombre': user['nombre_usuario']})
        else:
            return jsonify({'status': 'error'})
    except Exception as e:
        return jsonify({'status': 'error'}), 500

# =====================================================================
# MÓDULO DE OCUPACIÓN
# =====================================================================
@prod_chrysopa_bp.route('/ocupacion')
def ocupacion():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT P.id_detallechr, P.id_lote, P.semana, P.fecha_registro, U.nombre_usuario
            FROM PROD_DETALLE_CHRYSOPA P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            ORDER BY P.id_detallechr DESC LIMIT 1
        """)
        ultimo_lote = cursor.fetchone()

        resumen_ultimo = None
        if ultimo_lote:
            id_cabecera = ultimo_lote['id_detallechr']
            cursor.execute("SELECT numero_orificio, cantidad FROM OCUPACION WHERE id_detallechr = ?", (id_cabecera,))
            orificios = cursor.fetchall()
            
            r1 = sum(1 for o in orificios if 1 <= o['numero_orificio'] <= 100 and o['cantidad'] > 0)
            r2 = sum(1 for o in orificios if 101 <= o['numero_orificio'] <= 200 and o['cantidad'] > 0)
            r3 = sum(1 for o in orificios if 201 <= o['numero_orificio'] <= 300 and o['cantidad'] > 0)
            promedio = round((r1 + r2 + r3) / 3, 1)

            resumen_ultimo = {
                'lote': ultimo_lote['id_lote'], 'semana': ultimo_lote['semana'],
                'fecha': datetime.strptime(ultimo_lote['fecha_registro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M %p'),
                'operador': ultimo_lote['nombre_usuario'], 'r1': r1, 'r2': r2, 'r3': r3,
                'promedio': promedio, 'estatus': "Aceptado" if promedio >= 90.0 else "Revisión / Bajo"
            }

        cursor.execute("""
            SELECT P.id_detallechr, P.semana, P.fecha_registro, U.nombre_usuario
            FROM PROD_DETALLE_CHRYSOPA P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            ORDER BY P.id_detallechr DESC LIMIT 10
        """)
        historial = []
        for fila in cursor.fetchall():
            cursor.execute("SELECT numero_orificio, cantidad FROM OCUPACION WHERE id_detallechr = ?", (fila['id_detallechr'],))
            orifs = cursor.fetchall()
            if orifs:
                h1 = sum(1 for o in orifs if 1 <= o['numero_orificio'] <= 100 and o['cantidad'] > 0)
                h2 = sum(1 for o in orifs if 101 <= o['numero_orificio'] <= 200 and o['cantidad'] > 0)
                h3 = sum(1 for o in orifs if 201 <= o['numero_orificio'] <= 300 and o['cantidad'] > 0)
                historial.append({
                    'semana': fila['semana'], 'operador': fila['nombre_usuario'],
                    'fecha': datetime.strptime(fila['fecha_registro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M %p'),
                    'porcentaje': round((h1 + h2 + h3) / 3, 1)
                })
        conn.close()
    except Exception as e:
        resumen_ultimo = None; historial = []

    return render_template('produccion/chrysopa/ocupacion.html', ultimo=resumen_ultimo, historial=historial)

@prod_chrysopa_bp.route('/ocupacion/guardar', methods=['POST'])
def guardar_ocupacion():
    datos = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario FROM USUARIOS WHERE nip_firma = ? AND estatus = 'Activo'", (datos.get('nip'),))
        operador = cursor.fetchone()
        if not operador: return jsonify({'status': 'error', 'message': 'NIP Incorrecto'}), 403

        cursor.execute("INSERT INTO PROD_DETALLE_CHRYSOPA (id_lote, semana, id_operador, fecha_registro) VALUES (?, ?, ?, ?)",
                       (datos.get('lote'), datos.get('semana'), operador['id_usuario'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        id_cab = cursor.lastrowid

        for i, cant in enumerate(datos.get('rejillas'), start=1):
            cursor.execute("INSERT INTO OCUPACION (id_detallechr, numero_orificio, cantidad) VALUES (?, ?, ?)", (id_cab, i, cant))
        conn.commit(); conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# =====================================================================
# MÓDULO DE PUPACIÓN (Independiente usando la tabla PUPACION)
# =====================================================================
@prod_chrysopa_bp.route('/pupacion')
def pupacion():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Solo busca registros que tengan datos exclusivos en la tabla PUPACION
        cursor.execute("""
            SELECT P.id_detallechr, P.id_lote, P.semana, P.fecha_registro, U.nombre_usuario
            FROM PROD_DETALLE_CHRYSOPA P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            WHERE P.id_detallechr IN (SELECT DISTINCT id_detallechr FROM PUPACION)
            ORDER BY P.id_detallechr DESC LIMIT 1
        """)
        ultimo_lote = cursor.fetchone()

        resumen_ultimo = None
        if ultimo_lote:
            id_cabecera = ultimo_lote['id_detallechr']
            cursor.execute("SELECT numero_orificio, cantidad FROM PUPACION WHERE id_detallechr = ?", (id_cabecera,))
            orificios = cursor.fetchall()
            
            if orificios:
                r1 = sum(1 for o in orificios if 1 <= o['numero_orificio'] <= 100 and o['cantidad'] > 0)
                r2 = sum(1 for o in orificios if 101 <= o['numero_orificio'] <= 200 and o['cantidad'] > 0)
                r3 = sum(1 for o in orificios if 201 <= o['numero_orificio'] <= 300 and o['cantidad'] > 0)
                promedio = round((r1 + r2 + r3) / 3, 1)

                resumen_ultimo = {
                    'lote': ultimo_lote['id_lote'], 'semana': ultimo_lote['semana'],
                    'fecha': datetime.strptime(ultimo_lote['fecha_registro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M %p'),
                    'operador': ultimo_lote['nombre_usuario'], 'r1': r1, 'r2': r2, 'r3': r3,
                    'promedio': promedio, 'estatus': "Aceptado" if promedio >= 90.0 else "Revisión / Bajo"
                }

        cursor.execute("""
            SELECT P.id_detallechr, P.semana, P.fecha_registro, U.nombre_usuario
            FROM PROD_DETALLE_CHRYSOPA P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            WHERE P.id_detallechr IN (SELECT DISTINCT id_detallechr FROM PUPACION)
            ORDER BY P.id_detallechr DESC LIMIT 10
        """)
        historial = []
        for fila in cursor.fetchall():
            cursor.execute("SELECT numero_orificio, cantidad FROM PUPACION WHERE id_detallechr = ?", (fila['id_detallechr'],))
            orifs = cursor.fetchall()
            if orifs:
                h1 = sum(1 for o in orifs if 1 <= o['numero_orificio'] <= 100 and o['cantidad'] > 0)
                h2 = sum(1 for o in orifs if 101 <= o['numero_orificio'] <= 200 and o['cantidad'] > 0)
                h3 = sum(1 for o in orifs if 201 <= o['numero_orificio'] <= 300 and o['cantidad'] > 0)
                historial.append({
                    'semana': fila['semana'], 'operador': fila['nombre_usuario'],
                    'fecha': datetime.strptime(fila['fecha_registro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M %p'),
                    'porcentaje': round((h1 + h2 + h3) / 3, 1)
                })
        conn.close()
    except Exception as e:
        resumen_ultimo = None; historial = []

    return render_template('produccion/chrysopa/pupacion.html', ultimo=resumen_ultimo, historial=historial)


@prod_chrysopa_bp.route('/pupacion/guardar', methods=['POST'])
def guardar_pupacion():
    datos = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario FROM USUARIOS WHERE nip_firma = ? AND estatus = 'Activo'", (datos.get('nip'),))
        operador = cursor.fetchone()
        if not operador: return jsonify({'status': 'error', 'message': 'NIP Incorrecto'}), 403

        # Creamos la cabecera del lote
        cursor.execute("INSERT INTO PROD_DETALLE_CHRYSOPA (id_lote, semana, id_operador, fecha_registro) VALUES (?, ?, ?, ?)",
                       (datos.get('lote'), datos.get('semana'), operador['id_usuario'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        id_cab = cursor.lastrowid

        # Guardamos los 300 orificios exclusivamente en la tabla PUPACION
        for i, cant in enumerate(datos.get('rejillas'), start=1):
            cursor.execute("INSERT INTO PUPACION (id_detallechr, numero_orificio, cantidad) VALUES (?, ?, ?)", (id_cab, i, cant))
        conn.commit(); conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Otras rutas base...
# =====================================================================
# MÓDULO DE ECLOSIÓN
# =====================================================================
@prod_chrysopa_bp.route('/eclosion')
def eclosion():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Traer el último registro exclusivo de ECLOSIÓN
        cursor.execute("""
            SELECT P.id_detallechr, P.id_lote, P.semana, P.fecha_registro, U.nombre_usuario
            FROM PROD_DETALLE_CHRYSOPA P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            WHERE P.id_detallechr IN (SELECT DISTINCT id_detallechr FROM ECLOSION)
            ORDER BY P.id_detallechr DESC LIMIT 1
        """)
        ultimo_lote = cursor.fetchone()

        resumen_ultimo = None
        if ultimo_lote:
            id_cabecera = ultimo_lote['id_detallechr']
            cursor.execute("SELECT numero_orificio, cantidad FROM ECLOSION WHERE id_detallechr = ?", (id_cabecera,))
            orificios = cursor.fetchall()
            
            if orificios:
                r1 = sum(1 for o in orificios if 1 <= o['numero_orificio'] <= 100 and o['cantidad'] > 0)
                r2 = sum(1 for o in orificios if 101 <= o['numero_orificio'] <= 200 and o['cantidad'] > 0)
                r3 = sum(1 for o in orificios if 201 <= o['numero_orificio'] <= 300 and o['cantidad'] > 0)
                promedio = round((r1 + r2 + r3) / 3, 1)

                resumen_ultimo = {
                    'lote': ultimo_lote['id_lote'], 'semana': ultimo_lote['semana'],
                    'fecha': datetime.strptime(ultimo_lote['fecha_registro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M %p'),
                    'operador': ultimo_lote['nombre_usuario'], 'r1': r1, 'r2': r2, 'r3': r3,
                    'promedio': promedio, 'estatus': "Aceptado" if promedio >= 90.0 else "Revisión / Bajo"
                }

        # Historial de Eclosión
        cursor.execute("""
            SELECT P.id_detallechr, P.semana, P.fecha_registro, U.nombre_usuario
            FROM PROD_DETALLE_CHRYSOPA P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            WHERE P.id_detallechr IN (SELECT DISTINCT id_detallechr FROM ECLOSION)
            ORDER BY P.id_detallechr DESC LIMIT 10
        """)
        historial = []
        for fila in cursor.fetchall():
            cursor.execute("SELECT numero_orificio, cantidad FROM ECLOSION WHERE id_detallechr = ?", (fila['id_detallechr'],))
            orifs = cursor.fetchall()
            if orifs:
                h1 = sum(1 for o in orifs if 1 <= o['numero_orificio'] <= 100 and o['cantidad'] > 0)
                h2 = sum(1 for o in orifs if 101 <= o['numero_orificio'] <= 200 and o['cantidad'] > 0)
                h3 = sum(1 for o in orifs if 201 <= o['numero_orificio'] <= 300 and o['cantidad'] > 0)
                historial.append({
                    'semana': fila['semana'], 'operador': fila['nombre_usuario'],
                    'fecha': datetime.strptime(fila['fecha_registro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M %p'),
                    'porcentaje': round((h1 + h2 + h3) / 3, 1)
                })
        conn.close()
    except Exception as e:
        resumen_ultimo = None; historial = []

    return render_template('produccion/chrysopa/eclosion.html', ultimo=resumen_ultimo, historial=historial)


@prod_chrysopa_bp.route('/eclosion/guardar', methods=['POST'])
def guardar_eclosion():
    datos = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario FROM USUARIOS WHERE nip_firma = ? AND estatus = 'Activo'", (datos.get('nip'),))
        operador = cursor.fetchone()
        if not operador: return jsonify({'status': 'error', 'message': 'NIP Incorrecto'}), 403

        # Cabecera
        cursor.execute("INSERT INTO PROD_DETALLE_CHRYSOPA (id_lote, semana, id_operador, fecha_registro) VALUES (?, ?, ?, ?)",
                       (datos.get('lote'), datos.get('semana'), operador['id_usuario'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        id_cab = cursor.lastrowid

        # Detalle en tabla ECLOSION
        for i, cant in enumerate(datos.get('rejillas'), start=1):
            cursor.execute("INSERT INTO ECLOSION (id_detallechr, numero_orificio, cantidad) VALUES (?, ?, ?)", (id_cab, i, cant))
        conn.commit(); conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@prod_chrysopa_bp.route('/mortalidad')
def mortalidad(): return render_template('produccion/chrysopa/mortalidad.html')

@prod_chrysopa_bp.route('/fallas')
def fallas(): return render_template('produccion/chrysopa/fallas.html')

@prod_chrysopa_bp.route('/materiales')
def materiales(): return render_template('produccion/materiales.html', origen='chrysopa', mis_solicitudes=[])