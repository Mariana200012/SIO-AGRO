from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import sqlite3

# Declaramos el blueprint principal del Administrador
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ==========================================
# FUNCIÓN VITAL: CONEXIÓN A LA BASE DE DATOS
# ==========================================
def get_db_connection():
    # Asegúrate de que la ruta coincida con la ubicación de tu BD
    conn = sqlite3.connect('Bd_SIO-AGRO.db', isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn

# ==========================================
# 1. PANEL PRINCIPAL (DASHBOARD)
# ==========================================
@admin_bp.route('/dashboard')
def dashboard():
    return render_template('index.html')


# ==========================================
# 2. MÓDULO CHRYSOPA (ADMINISTRADOR)
# ==========================================
@admin_bp.route('/ocupacion')
def ocupacion():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT P.id_detallechr, P.id_lote, P.semana, P.fecha_registro, U.nombre_usuario
            FROM PROD_DETALLE_CHRYSOPA P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            WHERE P.id_detallechr IN (SELECT DISTINCT id_detallechr FROM OCUPACION)
            ORDER BY P.id_detallechr DESC
        """)
        lotes = cursor.fetchall()
        
        historial = []
        suma_promedios = 0
        
        for lote in lotes:
            cursor.execute("SELECT numero_orificio, cantidad FROM OCUPACION WHERE id_detallechr = ?", (lote['id_detallechr'],))
            orificios = cursor.fetchall()
            
            r1 = sum(1 for o in orificios if 1 <= o['numero_orificio'] <= 100 and o['cantidad'] > 0)
            r2 = sum(1 for o in orificios if 101 <= o['numero_orificio'] <= 200 and o['cantidad'] > 0)
            r3 = sum(1 for o in orificios if 201 <= o['numero_orificio'] <= 300 and o['cantidad'] > 0)
            
            promedio = round((r1 + r2 + r3) / 3, 1)
            suma_promedios += promedio
            
            try:
                fecha_obj = datetime.strptime(lote['fecha_registro'], '%Y-%m-%d %H:%M:%S')
                fecha_str = fecha_obj.strftime('%d/%b/%Y - %I:%M %p')
                fecha_iso = fecha_obj.strftime('%Y-%m-%d')
            except:
                fecha_str = fecha_iso = lote['fecha_registro']
                
            estatus = "Óptimo" if promedio >= 80.0 else "Requiere Revisión"
            
            historial.append({
                'lote': lote['id_lote'], 'semana': lote['semana'],
                'fecha_str': fecha_str, 'fecha_iso': fecha_iso, 'operador': lote['nombre_usuario'],
                'r1': r1, 'r2': r2, 'r3': r3, 'promedio': promedio, 'estatus': estatus
            })
            
        promedio_global = round(suma_promedios / len(historial), 1) if historial else 0.0
        conn.close()
    except Exception as e:
        print("Error en admin ocupación:", e)
        historial = []; promedio_global = 0.0

    return render_template('admin/chrysopa/ocupacion.html', historial=historial, promedio_global=promedio_global)

@admin_bp.route('/pupacion')
def pupacion():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT P.id_detallechr, P.id_lote, P.semana, P.fecha_registro, U.nombre_usuario
            FROM PROD_DETALLE_CHRYSOPA P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            WHERE P.id_detallechr IN (SELECT DISTINCT id_detallechr FROM PUPACION)
            ORDER BY P.id_detallechr DESC
        """)
        lotes = cursor.fetchall()
        
        historial = []
        suma_promedios = 0
        
        for lote in lotes:
            cursor.execute("SELECT numero_orificio, cantidad FROM PUPACION WHERE id_detallechr = ?", (lote['id_detallechr'],))
            orificios = cursor.fetchall()
            
            r1 = sum(1 for o in orificios if 1 <= o['numero_orificio'] <= 100 and o['cantidad'] > 0)
            r2 = sum(1 for o in orificios if 101 <= o['numero_orificio'] <= 200 and o['cantidad'] > 0)
            r3 = sum(1 for o in orificios if 201 <= o['numero_orificio'] <= 300 and o['cantidad'] > 0)
            
            promedio = round((r1 + r2 + r3) / 3, 1)
            suma_promedios += promedio
            
            try:
                fecha_obj = datetime.strptime(lote['fecha_registro'], '%Y-%m-%d %H:%M:%S')
                fecha_str = fecha_obj.strftime('%d/%b/%Y - %I:%M %p')
                fecha_iso = fecha_obj.strftime('%Y-%m-%d')
            except:
                fecha_str = fecha_iso = lote['fecha_registro']
                
            estatus = "Óptimo" if promedio >= 80.0 else "Requiere Revisión"
            
            historial.append({
                'lote': lote['id_lote'], 'semana': lote['semana'],
                'fecha_str': fecha_str, 'fecha_iso': fecha_iso, 'operador': lote['nombre_usuario'],
                'r1': r1, 'r2': r2, 'r3': r3, 'promedio': promedio, 'estatus': estatus
            })
            
        promedio_global = round(suma_promedios / len(historial), 1) if historial else 0.0
        conn.close()
    except Exception as e:
        print("Error en admin pupación:", e)
        historial = []; promedio_global = 0.0

    return render_template('admin/chrysopa/pupacion.html', historial=historial, promedio_global=promedio_global)

@admin_bp.route('/eclosion')
def eclosion():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT P.id_detallechr, P.id_lote, P.semana, P.fecha_registro, U.nombre_usuario
            FROM PROD_DETALLE_CHRYSOPA P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            WHERE P.id_detallechr IN (SELECT DISTINCT id_detallechr FROM ECLOSION)
            ORDER BY P.id_detallechr DESC
        """)
        lotes = cursor.fetchall()
        
        historial = []
        suma_promedios = 0
        
        for lote in lotes:
            cursor.execute("SELECT numero_orificios, cantidad FROM ECLOSION WHERE id_detallechr = ?", (lote['id_detallechr'],))
            orificios = cursor.fetchall()
            
            r1 = sum(1 for o in orificios if 1 <= o['numero_orificios'] <= 100 and o['cantidad'] > 0)
            r2 = sum(1 for o in orificios if 101 <= o['numero_orificios'] <= 200 and o['cantidad'] > 0)
            r3 = sum(1 for o in orificios if 201 <= o['numero_orificios'] <= 300 and o['cantidad'] > 0)
            
            promedio = round((r1 + r2 + r3) / 3, 1)
            suma_promedios += promedio
            
            try:
                fecha_obj = datetime.strptime(lote['fecha_registro'], '%Y-%m-%d %H:%M:%S')
                fecha_str = fecha_obj.strftime('%d/%b/%Y - %I:%M %p')
                fecha_iso = fecha_obj.strftime('%Y-%m-%d')
            except:
                fecha_str = fecha_iso = lote['fecha_registro']
                
            estatus = "Óptimo" if promedio >= 70.0 else "Requiere Revisión"
            
            historial.append({
                'lote': lote['id_lote'], 'semana': lote['semana'],
                'fecha_str': fecha_str, 'fecha_iso': fecha_iso, 'operador': lote['nombre_usuario'],
                'r1': r1, 'r2': r2, 'r3': r3, 'promedio': promedio, 'estatus': estatus
            })
            
        promedio_global = round(suma_promedios / len(historial), 1) if historial else 0.0
        conn.close()
    except Exception as e:
        print("Error en admin eclosión:", e)
        historial = []; promedio_global = 0.0

    return render_template('admin/chrysopa/eclosion.html', historial=historial, promedio_global=promedio_global)

@admin_bp.route('/mortalidad')
def mortalidad():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT P.id_detallechr, P.id_lote, P.semana, P.fecha_registro, U.nombre_usuario
            FROM PROD_DETALLE_CHRYSOPA P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            WHERE P.id_detallechr IN (SELECT DISTINCT id_detallechr FROM MORTALIDAD_BOTES)
            ORDER BY P.id_detallechr DESC
        """)
        lotes = cursor.fetchall()
        
        historial = []
        suma_promedios = 0
        
        for lote in lotes:
            cursor.execute("SELECT numero_bote, cant_muertos FROM MORTALIDAD_BOTES WHERE id_detallechr = ?", (lote['id_detallechr'],))
            botes = {fila['numero_bote']: fila['cant_muertos'] for fila in cursor.fetchall()}
            
            r1 = botes.get(1, 0); r2 = botes.get(2, 0); r3 = botes.get(3, 0)
            r4 = botes.get(4, 0); r5 = botes.get(5, 0); r6 = botes.get(6, 0)
            
            promedio = round((r1 + r2 + r3 + r4 + r5 + r6) / 6, 1)
            suma_promedios += promedio
            
            try:
                fecha_obj = datetime.strptime(lote['fecha_registro'], '%Y-%m-%d %H:%M:%S')
                fecha_str = fecha_obj.strftime('%d/%b/%Y - %I:%M %p')
                fecha_iso = fecha_obj.strftime('%Y-%m-%d')
            except:
                fecha_str = fecha_iso = lote['fecha_registro']
                
            estatus = "Tolerable" if promedio <= 15.0 else "Requiere Revisión"
            
            historial.append({
                'lote': lote['id_lote'], 'semana': lote['semana'],
                'fecha_str': fecha_str, 'fecha_iso': fecha_iso, 'operador': lote['nombre_usuario'],
                'r1': r1, 'r2': r2, 'r3': r3, 'r4': r4, 'r5': r5, 'r6': r6, 
                'promedio': promedio, 'estatus': estatus
            })
            
        promedio_global = round(suma_promedios / len(historial), 1) if historial else 0.0
        conn.close()
    except Exception as e:
        print("Error en admin mortalidad:", e)
        historial = []; promedio_global = 0.0

    return render_template('admin/chrysopa/mortalidad.html', historial=historial, promedio_global=promedio_global)

@admin_bp.route('/fallas')
def fallas():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT P.id_detallechr, P.id_lote, P.semana, P.fecha_registro, U.nombre_usuario
            FROM PROD_DETALLE_CHRYSOPA P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            WHERE P.id_detallechr IN (SELECT DISTINCT id_detallechr FROM FALLA_PUPACION)
            ORDER BY P.id_detallechr DESC
        """)
        lotes = cursor.fetchall()
        
        historial = []
        suma_promedios = 0
        
        for lote in lotes:
            cursor.execute("SELECT numero_rejilla, larvas_no_pupadas FROM FALLA_PUPACION WHERE id_detallechr = ?", (lote['id_detallechr'],))
            rejillas = {fila['numero_rejilla']: fila['larvas_no_pupadas'] for fila in cursor.fetchall()}
            
            r1 = rejillas.get(1, 0); r2 = rejillas.get(2, 0); r3 = rejillas.get(3, 0)
            r4 = rejillas.get(4, 0); r5 = rejillas.get(5, 0); r6 = rejillas.get(6, 0)
            
            promedio = round((r1 + r2 + r3 + r4 + r5 + r6) / 6, 1)
            suma_promedios += promedio
            
            try:
                fecha_obj = datetime.strptime(lote['fecha_registro'], '%Y-%m-%d %H:%M:%S')
                fecha_str = fecha_obj.strftime('%d/%b/%Y - %I:%M %p')
                fecha_iso = fecha_obj.strftime('%Y-%m-%d')
            except:
                fecha_str = fecha_iso = lote['fecha_registro']
                
            estatus = "Tolerable" if promedio <= 10.0 else "Requiere Revisión"
            
            historial.append({
                'lote': lote['id_lote'], 'semana': lote['semana'],
                'fecha_str': fecha_str, 'fecha_iso': fecha_iso, 'operador': lote['nombre_usuario'],
                'r1': r1, 'r2': r2, 'r3': r3, 'r4': r4, 'r5': r5, 'r6': r6, 
                'promedio': promedio, 'estatus': estatus
            })
            
        promedio_global = round(suma_promedios / len(historial), 1) if historial else 0.0
        conn.close()
    except Exception as e:
        print("Error en admin fallas:", e)
        historial = []; promedio_global = 0.0

    return render_template('admin/chrysopa/fallas.html', historial=historial, promedio_global=promedio_global)


# =====================================================================
# 3. MÓDULO CATOPAR (ADMINISTRADOR)
# =====================================================================
@admin_bp.route('/catopar/pre')
def catopar_pre():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT P.id_lote, P.viables, P.porcentaje, P.fecha_registro, U.nombre_usuario
            FROM PRE_PARASITISMO P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            ORDER BY P.fecha_registro DESC
        """)
        filas = cursor.fetchall()
        
        historial = [] 
        suma_porcentajes = 0
        
        for f in filas:
            try:
                fecha_obj = datetime.strptime(f['fecha_registro'], '%Y-%m-%d %H:%M:%S')
                fecha_str = fecha_obj.strftime('%d/%b/%Y - %I:%M %p')
                fecha_iso = fecha_obj.strftime('%Y-%m-%d')
            except:
                fecha_str = fecha_iso = f['fecha_registro']
                
            porcentaje = f['porcentaje']
            suma_porcentajes += porcentaje
            
            historial.append({
                'id_lote': f['id_lote'],
                'viables': f['viables'],
                'porcentaje': round(porcentaje, 1),
                'fecha_str': fecha_str,
                'fecha_iso': fecha_iso,
                'operador': f['nombre_usuario']
            })
            
        promedio_global = round(suma_porcentajes / len(historial), 1) if historial else 0.0
        conn.close()
        
    except Exception as e:
        print("Error en Admin Catopar Pre:", e)
        historial = []
        promedio_global = 0.0
        
    return render_template('admin/catopar/pre.html', historial=historial, promedio_global=promedio_global)


@admin_bp.route('/catopar/post')
def catopar_post():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                C.id_cabecera, C.id_lote, C.fecha_registro, U.nombre_usuario,
                SUM(D.gorg_nacidos) as total_gorg_nacidos,
                SUM(D.gorg_pupas) as total_gorg_pupas,
                SUM(D.cat_negros) as total_cat_negros,
                SUM(D.cat_combinados) as total_cat_combinados,
                SUM(D.cat_ambar) as total_cat_ambar
            FROM POST_PARASITISMO_CABECERA C
            JOIN USUARIOS U ON C.id_operador = U.id_usuario
            LEFT JOIN POST_PARASITISMO_DETALLE D ON C.id_cabecera = D.id_cabecera
            GROUP BY C.id_cabecera
            ORDER BY C.fecha_registro DESC
        """)
        filas = cursor.fetchall()
        
        historial = []
        total_parasitismo = 0
        total_evaluados = 0
        
        for f in filas:
            t_gorg = (f['total_gorg_nacidos'] or 0) + (f['total_gorg_pupas'] or 0)
            t_cat = (f['total_cat_negros'] or 0) + (f['total_cat_combinados'] or 0) + (f['total_cat_ambar'] or 0)
            total_insectos = t_gorg + t_cat
            
            porcentaje = (t_cat / total_insectos * 100) if total_insectos > 0 else 0
            
            try:
                fecha_obj = datetime.strptime(f['fecha_registro'], '%Y-%m-%d %H:%M:%S')
                fecha_str = fecha_obj.strftime('%d/%b/%Y - %I:%M %p')
                fecha_iso = fecha_obj.strftime('%Y-%m-%d')
            except:
                fecha_str = fecha_iso = f['fecha_registro']
            
            historial.append({
                'id_lote': f['id_lote'],
                't_gorg': t_gorg,
                't_cat': t_cat,
                'total_insectos': total_insectos,
                'porcentaje': round(porcentaje, 1),
                'fecha_str': fecha_str,
                'fecha_iso': fecha_iso,
                'operador': f['nombre_usuario']
            })
            
            total_parasitismo += t_cat
            total_evaluados += total_insectos
            
        promedio_global = round((total_parasitismo / total_evaluados) * 100, 1) if total_evaluados > 0 else 0.0
            
        conn.close()
    except Exception as e:
        print("Error en Admin Catopar Post:", e)
        historial = []
        promedio_global = 0.0
        
    return render_template('admin/catopar/post.html', historial=historial, promedio_global=promedio_global)

@admin_bp.route('/catopar/post/asignar', methods=['POST'])
def catopar_asignar():
    id_lote = request.form.get('id_lote')
    botes_madre = request.form.get('botes_madre', type=int)
    botes_parasitar = request.form.get('botes_parasitar', type=int)
    id_admin = session.get('id_usuario')
    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO PROD_ASIGNACION_CATOPAR 
            (id_lote, botes_cria_madre, botes_a_parasitar, id_administrador, fecha_asignacion) 
            VALUES (?, ?, ?, ?, ?)
        """, (id_lote, botes_madre, botes_parasitar, id_admin, fecha_actual))
        
        conn.commit()
        flash(f'Asignación guardada para el lote {id_lote}', 'success')
    except Exception as e:
        print("Error al asignar botes:", e)
        flash('Hubo un error al guardar la asignación.', 'error')
    finally:
        if 'conn' in locals():
            conn.close()

    return redirect(url_for('admin.catopar_post'))


# ==========================================
# 4. RUTAS NUEVAS PARA EL MENÚ (DASHBOARD Y ASISTENCIA)
# ==========================================
@admin_bp.route('/metricas')
def metricas():
    if session.get('id_area') != 5:
        flash('Acceso denegado. Área exclusiva de Administración.', 'error')
        return redirect(url_for('auth.login'))
        
    return render_template('admin/dashboard.html')

@admin_bp.route('/asistencia')
def asistencia():
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total FROM USUARIOS")
    total_operadores = cursor.fetchone()['total']

    cursor.execute("""
        SELECT U.nombre_usuario, A.hora_entrada, C.nombre_area
        FROM ASISTENCIA A
        JOIN USUARIOS U ON A.id_usuario = U.id_usuario
        LEFT JOIN CAT_AREAS C ON U.id_area = C.id_area
        WHERE A.fecha = ? AND A.hora_entrada IS NOT NULL
        ORDER BY C.nombre_area DESC, A.hora_entrada DESC 
    """, (fecha_hoy,))
    
    filas_registros = cursor.fetchall()
    conn.close()

    # Formatear la hora de entrada a formato de 12 horas con AM/PM
    registros = []
    for r in filas_registros:
        r_dict = dict(r)
        if r_dict['hora_entrada']:
            try:
                for fmt in ('%H:%M:%S', '%H:%M'):
                    try:
                        dt = datetime.strptime(r_dict['hora_entrada'], fmt)
                        r_dict['hora_entrada'] = dt.strftime('%I:%M %p')
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
        registros.append(r_dict)

    total_presentes = len(registros)
    chrysopa_count = sum(1 for r in registros if r['nombre_area'] and 'Chrysopa' in r['nombre_area'])
    catopar_count = sum(1 for r in registros if r['nombre_area'] and 'Catopar' in r['nombre_area'])
    otros_count = total_presentes - chrysopa_count - catopar_count

    return render_template('admin/asistencia.html', 
                           registros=registros,
                           total_presentes=total_presentes,
                           total_operadores=total_operadores,
                           chrysopa_count=chrysopa_count,
                           catopar_count=catopar_count,
                           otros_count=otros_count)


# ==========================================
# 5. GESTIÓN DE USUARIOS (Conexión a SQLite)
# ==========================================
@admin_bp.route('/usuarios')
def usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.id_usuario, u.nombre_usuario, u.puesto, u.nip_firma, u.id_area, a.nombre_area 
        FROM USUARIOS u
        LEFT JOIN CAT_AREAS a ON u.id_area = a.id_area
        WHERE u.estatus = 'Activo'
    """)
    lista_usuarios = cursor.fetchall()
    conn.close()
    
    return render_template('admin/usuarios.html', usuarios=lista_usuarios)

@admin_bp.route('/usuarios/agregar', methods=['POST'])
def agregar_usuario():
    nombre = request.form['nombre_usuario']
    puesto = request.form['puesto']
    nip = request.form['nip_firma']
    id_area = request.form['id_area']
    
    conexion = get_db_connection()
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO USUARIOS (id_area, nombre_usuario, puesto, nip_firma) VALUES (?, ?, ?, ?)",
        (id_area, nombre, puesto, nip)
    )
    conexion.commit()
    conexion.close()
    
    return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/eliminar/<int:id_usuario>', methods=['POST'])
def eliminar_usuario(id_usuario):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id_area FROM USUARIOS WHERE id_usuario = ?", (id_usuario,))
        usuario = cursor.fetchone()

        if usuario and str(usuario['id_area']).strip() == '5':
            cursor.execute("SELECT COUNT(*) as total FROM USUARIOS WHERE (id_area = 5 OR id_area = '5') AND estatus = 'Activo'")
            total_admins = cursor.fetchone()['total']

            if total_admins <= 1:
                flash('Acción denegada: No puedes dar de baja al único Administrador.', 'error')
                return redirect(url_for('admin.usuarios'))

        cursor.execute("UPDATE USUARIOS SET estatus = 'Inactivo' WHERE id_usuario = ?", (id_usuario,))
        flash('Operador dado de baja correctamente.', 'success')

    except Exception as e:
        flash(f'Error al dar de baja: {str(e)}', 'error')
    finally:
        conn.close()

    return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/editar/<int:id_usuario>', methods=['POST'])
def editar_usuario(id_usuario):
    nombre_usuario = request.form.get('nombre_usuario')
    puesto_nuevo = request.form.get('puesto')
    nip_firma = request.form.get('nip_firma')
    nuevo_id_area = request.form.get('id_area')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF;")

        cursor.execute("SELECT id_area, puesto, estatus FROM USUARIOS WHERE id_usuario = ?", (id_usuario,))
        usuario_actual = cursor.fetchone()
        
        if not usuario_actual:
            return redirect(url_for('admin.usuarios'))
            
        area_actual = str(usuario_actual['id_area']).strip()
        nuevo_id_area = str(nuevo_id_area).strip() if nuevo_id_area else area_actual
        puesto_nuevo = str(puesto_nuevo).strip() if puesto_nuevo else str(usuario_actual['puesto']).strip()

        if area_actual == '5' and usuario_actual['estatus'] == 'Activo':
            if nuevo_id_area != '5' or puesto_nuevo.lower() != 'administrador':
                cursor.execute("SELECT COUNT(*) as total FROM USUARIOS WHERE CAST(id_area AS TEXT) = '5' AND estatus = 'Activo'")
                total_admins = cursor.fetchone()['total']
                if total_admins <= 1:
                    flash('Acción denegada: Eres el único Administrador activo. No puedes cambiar tu Puesto ni tu Área.', 'error')
                    return redirect(url_for('admin.usuarios'))

        cursor.execute("""
            UPDATE USUARIOS 
            SET nombre_usuario = ?, puesto = ?, nip_firma = ?, id_area = ?
            WHERE id_usuario = ?
        """, (nombre_usuario, puesto_nuevo, nip_firma, nuevo_id_area, id_usuario))
        
        flash('Datos del usuario actualizados correctamente.', 'success')

    except Exception as e:
        flash(f'Error al actualizar: {str(e)}', 'error')
    finally:
        conn.close()

    return redirect(url_for('admin.usuarios'))