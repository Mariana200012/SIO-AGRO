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

            try:
                f_bonita = datetime.strptime(ultimo_lote['fecha_registro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M %p')
            except:
                f_bonita = ultimo_lote['fecha_registro']

            resumen_ultimo = {
                'lote': ultimo_lote['id_lote'], 'semana': ultimo_lote['semana'],
                'fecha': f_bonita,
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
                
                try:
                    f_bonita = datetime.strptime(fila['fecha_registro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M %p')
                except:
                    f_bonita = fila['fecha_registro']

                historial.append({
                    'semana': fila['semana'], 'operador': fila['nombre_usuario'],
                    'fecha': f_bonita,
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

                try:
                    f_bonita = datetime.strptime(ultimo_lote['fecha_registro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M %p')
                except:
                    f_bonita = ultimo_lote['fecha_registro']

                resumen_ultimo = {
                    'lote': ultimo_lote['id_lote'], 'semana': ultimo_lote['semana'],
                    'fecha': f_bonita,
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
                
                try:
                    f_bonita = datetime.strptime(fila['fecha_registro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M %p')
                except:
                    f_bonita = fila['fecha_registro']

                historial.append({
                    'semana': fila['semana'], 'operador': fila['nombre_usuario'],
                    'fecha': f_bonita,
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

        cursor.execute("INSERT INTO PROD_DETALLE_CHRYSOPA (id_lote, semana, id_operador, fecha_registro) VALUES (?, ?, ?, ?)",
                       (datos.get('lote'), datos.get('semana'), operador['id_usuario'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        id_cab = cursor.lastrowid

        for i, cant in enumerate(datos.get('rejillas'), start=1):
            cursor.execute("INSERT INTO PUPACION (id_detallechr, numero_orificio, cantidad) VALUES (?, ?, ?)", (id_cab, i, cant))
        conn.commit(); conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# =====================================================================
# MÓDULO DE ECLOSIÓN
# =====================================================================
@prod_chrysopa_bp.route('/eclosion')
def eclosion():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

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

                try:
                    f_bonita = datetime.strptime(ultimo_lote['fecha_registro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M %p')
                except:
                    f_bonita = ultimo_lote['fecha_registro']

                resumen_ultimo = {
                    'lote': ultimo_lote['id_lote'], 'semana': ultimo_lote['semana'],
                    'fecha': f_bonita,
                    'operador': ultimo_lote['nombre_usuario'], 'r1': r1, 'r2': r2, 'r3': r3,
                    'promedio': promedio, 'estatus': "Aceptado" if promedio >= 90.0 else "Revisión / Bajo"
                }

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
                
                try:
                    f_bonita = datetime.strptime(fila['fecha_registro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M %p')
                except:
                    f_bonita = fila['fecha_registro']

                historial.append({
                    'semana': fila['semana'], 'operador': fila['nombre_usuario'],
                    'fecha': f_bonita,
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

        cursor.execute("INSERT INTO PROD_DETALLE_CHRYSOPA (id_lote, semana, id_operador, fecha_registro) VALUES (?, ?, ?, ?)",
                       (datos.get('lote'), datos.get('semana'), operador['id_usuario'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        id_cab = cursor.lastrowid

        for i, cant in enumerate(datos.get('rejillas'), start=1):
            cursor.execute("INSERT INTO ECLOSION (id_detallechr, numero_orificio, cantidad) VALUES (?, ?, ?)", (id_cab, i, cant))
        conn.commit(); conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# =====================================================================
# MÓDULO DE MORTALIDAD (Conteo directo en 6 Botes)
# =====================================================================
@prod_chrysopa_bp.route('/mortalidad')
def mortalidad():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT P.id_detallechr, P.id_lote, P.semana, P.fecha_registro, U.nombre_usuario
            FROM PROD_DETALLE_CHRYSOPA P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            WHERE P.id_detallechr IN (SELECT DISTINCT id_detallechr FROM MORTALIDAD_BOTES)
            ORDER BY P.id_detallechr DESC LIMIT 1
        """)
        ultimo_lote = cursor.fetchone()

        resumen_ultimo = None
        if ultimo_lote:
            id_cabecera = ultimo_lote['id_detallechr']
            cursor.execute("SELECT numero_bote, cant_muertos FROM MORTALIDAD_BOTES WHERE id_detallechr = ?", (id_cabecera,))
            botes = {fila['numero_bote']: fila['cant_muertos'] for fila in cursor.fetchall()}
            
            r1 = botes.get(1, 0); r2 = botes.get(2, 0); r3 = botes.get(3, 0)
            r4 = botes.get(4, 0); r5 = botes.get(5, 0); r6 = botes.get(6, 0)
            
            promedio = round((r1 + r2 + r3 + r4 + r5 + r6) / 6, 1)
            estatus_calidad = "Tolerable" if promedio <= 15.0 else "Revisión / Alto"

            try:
                f_bonita = datetime.strptime(ultimo_lote['fecha_registro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M %p')
            except:
                f_bonita = ultimo_lote['fecha_registro']
            
            resumen_ultimo = {
                'lote': ultimo_lote['id_lote'], 'semana': ultimo_lote['semana'],
                'fecha': f_bonita, 'operador': ultimo_lote['nombre_usuario'],
                'r1': r1, 'r2': r2, 'r3': r3, 'r4': r4, 'r5': r5, 'r6': r6,
                'promedio': promedio, 'estatus': estatus_calidad
            }

        cursor.execute("""
            SELECT P.id_detallechr, P.id_lote, P.semana, P.fecha_registro, U.nombre_usuario
            FROM PROD_DETALLE_CHRYSOPA P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            WHERE P.id_detallechr IN (SELECT DISTINCT id_detallechr FROM MORTALIDAD_BOTES)
            ORDER BY P.id_detallechr DESC LIMIT 10
        """)
        historial = []
        for fila in cursor.fetchall():
            cursor.execute("SELECT SUM(cant_muertos) as total_muertos FROM MORTALIDAD_BOTES WHERE id_detallechr = ?", (fila['id_detallechr'],))
            total_muertos = cursor.fetchone()['total_muertos'] or 0
            promedio_historial = round(total_muertos / 6, 1)

            try:
                f_bonita = datetime.strptime(fila['fecha_registro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M %p')
            except:
                f_bonita = fila['fecha_registro']

            historial.append({
                'lote': fila['id_lote'], 'semana': fila['semana'], 'operador': fila['nombre_usuario'],
                'fecha': f_bonita, 'porcentaje': promedio_historial
            })
        conn.close()
    except Exception as e:
        print("Error en mortalidad:", e)
        resumen_ultimo = None; historial = []

    return render_template('produccion/chrysopa/mortalidad.html', ultimo=resumen_ultimo, historial=historial)


@prod_chrysopa_bp.route('/mortalidad/guardar', methods=['POST'])
def guardar_mortalidad():
    datos = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario FROM USUARIOS WHERE nip_firma = ? AND estatus = 'Activo'", (datos.get('nip'),))
        operador = cursor.fetchone()
        if not operador: return jsonify({'status': 'error', 'message': 'NIP Incorrecto'}), 403

        semana_revision = datos.get('semana')

        cursor.execute("INSERT INTO PROD_DETALLE_CHRYSOPA (id_lote, semana, id_operador, fecha_registro) VALUES (?, ?, ?, ?)",
                       (datos.get('lote'), semana_revision, operador['id_usuario'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        id_cab = cursor.lastrowid

        for i, cant in enumerate(datos.get('botes'), start=1):
            cursor.execute("INSERT INTO MORTALIDAD_BOTES (id_detallechr, semana_revision, numero_bote, cant_muertos) VALUES (?, ?, ?, ?)", (id_cab, semana_revision, i, cant))
        
        conn.commit(); conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# =====================================================================
# MÓDULO DE FALLAS DE PUPACIÓN (Conteo directo en 6 Rejillas)
# =====================================================================
@prod_chrysopa_bp.route('/fallas')
def fallas():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT P.id_detallechr, P.id_lote, P.semana, P.fecha_registro, U.nombre_usuario
            FROM PROD_DETALLE_CHRYSOPA P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            WHERE P.id_detallechr IN (SELECT DISTINCT id_detallechr FROM FALLA_PUPACION)
            ORDER BY P.id_detallechr DESC LIMIT 1
        """)
        ultimo_lote = cursor.fetchone()

        resumen_ultimo = None
        if ultimo_lote:
            id_cabecera = ultimo_lote['id_detallechr']
            cursor.execute("SELECT numero_rejilla, larvas_no_pupadas FROM FALLA_PUPACION WHERE id_detallechr = ?", (id_cabecera,))
            rejillas = {fila['numero_rejilla']: fila['larvas_no_pupadas'] for fila in cursor.fetchall()}
            
            r1 = rejillas.get(1, 0); r2 = rejillas.get(2, 0); r3 = rejillas.get(3, 0)
            r4 = rejillas.get(4, 0); r5 = rejillas.get(5, 0); r6 = rejillas.get(6, 0)
            
            promedio = round((r1 + r2 + r3 + r4 + r5 + r6) / 6, 1)
            estatus_calidad = "Tolerable" if promedio <= 10.0 else "Revisión / Alto"

            try:
                f_bonita = datetime.strptime(ultimo_lote['fecha_registro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M %p')
            except:
                f_bonita = ultimo_lote['fecha_registro']
            
            resumen_ultimo = {
                'lote': ultimo_lote['id_lote'], 'semana': ultimo_lote['semana'],
                'fecha': f_bonita, 'operador': ultimo_lote['nombre_usuario'],
                'r1': r1, 'r2': r2, 'r3': r3, 'r4': r4, 'r5': r5, 'r6': r6,
                'promedio': promedio, 'estatus': estatus_calidad
            }

        cursor.execute("""
            SELECT P.id_detallechr, P.id_lote, P.semana, P.fecha_registro, U.nombre_usuario
            FROM PROD_DETALLE_CHRYSOPA P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            WHERE P.id_detallechr IN (SELECT DISTINCT id_detallechr FROM FALLA_PUPACION)
            ORDER BY P.id_detallechr DESC LIMIT 10
        """)
        historial = []
        for fila in cursor.fetchall():
            cursor.execute("SELECT SUM(larvas_no_pupadas) as total_fallas FROM FALLA_PUPACION WHERE id_detallechr = ?", (fila['id_detallechr'],))
            total_fallas = cursor.fetchone()['total_fallas'] or 0
            promedio_historial = round(total_fallas / 6, 1)

            try:
                f_bonita = datetime.strptime(fila['fecha_registro'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M %p')
            except:
                f_bonita = fila['fecha_registro']

            historial.append({
                'lote': fila['id_lote'], 'semana': fila['semana'], 'operador': fila['nombre_usuario'],
                'fecha': f_bonita, 'porcentaje': promedio_historial
            })
        conn.close()
    except Exception as e:
        print("Error en fallas:", e)
        resumen_ultimo = None; historial = []

    return render_template('produccion/chrysopa/fallas.html', ultimo=resumen_ultimo, historial=historial)


@prod_chrysopa_bp.route('/fallas/guardar', methods=['POST'])
def guardar_fallas():
    datos = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario FROM USUARIOS WHERE nip_firma = ? AND estatus = 'Activo'", (datos.get('nip'),))
        operador = cursor.fetchone()
        if not operador: return jsonify({'status': 'error', 'message': 'NIP Incorrecto'}), 403

        semana_origen = datos.get('semana')

        cursor.execute("INSERT INTO PROD_DETALLE_CHRYSOPA (id_lote, semana, id_operador, fecha_registro) VALUES (?, ?, ?, ?)",
                       (datos.get('lote'), semana_origen, operador['id_usuario'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        id_cab = cursor.lastrowid

        for i, cant in enumerate(datos.get('rejillas'), start=1):
            cursor.execute("INSERT INTO FALLA_PUPACION (id_detallechr, numero_rejilla, larvas_no_pupadas) VALUES (?, ?, ?)", (id_cab, i, cant))
        
        conn.commit(); conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# =====================================================================
# MÓDULO DE SOLICITUD DE MATERIALES
# =====================================================================
@prod_chrysopa_bp.route('/materiales')
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
            ORDER BY SM.id_solicitud DESC
        """)
        filas = cursor.fetchall()
        
        solicitudes_dict = {}
        for fila in filas:
            id_sol = fila['id_solicitud']
            if id_sol not in solicitudes_dict:
                fecha_formateada = fila['fecha_solicitud']
                if fecha_formateada:
                    try:
                        dt = datetime.strptime(fecha_formateada, '%Y-%m-%d %H:%M:%S')
                        fecha_formateada = dt.strftime('%d/%m/%Y %I:%M %p')
                    except ValueError:
                        pass

                solicitudes_dict[id_sol] = {
                    'id_solicitud': id_sol,
                    'fecha_solicitud': fecha_formateada,
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
        print("Error al cargar materiales:", e)

    return render_template('produccion/materiales.html', origen='chrysopa', mis_solicitudes=mis_solicitudes)


@prod_chrysopa_bp.route('/materiales/guardar', methods=['POST'])
def guardar_materiales():
    id_area = session.get('id_area', 1)  # Asume área 1 por default si no hay sesión
    nip_ingresado = request.form.get('nip')
    id_solicitud_editar = request.form.get('id_solicitud_editar')
    fecha_hora_mexico = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id_usuario, nombre_usuario FROM USUARIOS WHERE nip_firma = ? AND estatus = 'Activo'", (nip_ingresado,))
        operador_real = cursor.fetchone()
        
        if not operador_real:
            flash('NIP Incorrecto o usuario no activo.', 'error')
            return redirect(url_for('prod_chrysopa.materiales'))
            
        id_operador_real = operador_real['id_usuario']
        nombre_operador_real = operador_real['nombre_usuario']

        materiales_pedidos = []
        for i in range(1, 20):  
            if request.form.get(f'material_{i}'):
                cantidad = request.form.get(f'cant_{i}')
                if cantidad and int(cantidad) > 0:
                    materiales_pedidos.append({'id_material': i, 'cantidad': int(cantidad)})
                    
        if not materiales_pedidos:
            flash('Debes seleccionar al menos un material.', 'error')
            return redirect(url_for('prod_chrysopa.materiales'))

        if id_solicitud_editar:
            cursor.execute("UPDATE SOLICITUDES_MATERIAL SET estatus = 'Pendiente', fecha_solicitud = ?, id_operador = ? WHERE id_solicitud = ?", (fecha_hora_mexico, id_operador_real, id_solicitud_editar))
            cursor.execute("DELETE FROM SOLICITUDES_DETALLE WHERE id_solicitud = ?", (id_solicitud_editar,))
            for mat in materiales_pedidos:
                cursor.execute("INSERT INTO SOLICITUDES_DETALLE (id_solicitud, id_material, cantidad_solicitada) VALUES (?, ?, ?)", (id_solicitud_editar, mat['id_material'], mat['cantidad']))
            flash(f'Solicitud corregida por {nombre_operador_real}.', 'success')
        else:
            cursor.execute("INSERT INTO SOLICITUDES_MATERIAL (id_area_solicitante, id_operador, estatus, fecha_solicitud) VALUES (?, ?, 'Pendiente', ?)", (id_area, id_operador_real, fecha_hora_mexico))
            nuevo_folio = cursor.lastrowid
            for mat in materiales_pedidos:
                cursor.execute("INSERT INTO SOLICITUDES_DETALLE (id_solicitud, id_material, cantidad_solicitada) VALUES (?, ?, ?)", (nuevo_folio, mat['id_material'], mat['cantidad']))
            flash(f'Solicitud enviada por {nombre_operador_real}.', 'success')
            
        conn.commit()
    except Exception as e:
        if 'conn' in locals() and conn: conn.rollback()
        flash(f'Error al guardar solicitud: {str(e)}', 'error')
    finally:
        if 'conn' in locals() and conn: conn.close()
        
    return redirect(url_for('prod_chrysopa.materiales'))


@prod_chrysopa_bp.route('/materiales/detalle/<int:id_solicitud>')
def detalle_solicitud(id_solicitud):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_material, cantidad_solicitada FROM SOLICITUDES_DETALLE WHERE id_solicitud = ?", (id_solicitud,))
        filas = cursor.fetchall()
        datos = [{"id_material": f["id_material"], "cantidad": f["cantidad_solicitada"]} for f in filas]
        conn.close()
        return jsonify(datos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500