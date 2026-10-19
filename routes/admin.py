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
# DASHBOARD PRINCIPAL DEL ADMINISTRADOR
# ==========================================
@admin_bp.route('/metricas')
def metricas():
    # Inicia por defecto en Chrysopa
    return redirect(url_for('admin.dashb_chrysopa'))

@admin_bp.route('/metricas/chrysopa')
def dashb_chrysopa():
    return render_template('admin/dashb_chrysopa.html')

@admin_bp.route('/metricas/catopar')
def dashb_catopar():
    return render_template('admin/dashb_catopar.html')


# ==========================================
# MÓDULO CHRYSOPA
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
            # CORREGIDO: numero_orificio (singular)
            cursor.execute("SELECT numero_orificio, cantidad FROM ECLOSION WHERE id_detallechr = ?", (lote['id_detallechr'],))
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

    return render_template('admin/chrysopa/eclosion.html', historial=historial, promedio_global=promedio_global, ultimo=ultimo)
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
# MÓDULO CATOPAR 
# =====================================================================
@admin_bp.route('/catopar/pre')
def catopar_pre():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Leemos el historial incluyendo el estatus y semana
        cursor.execute("""
            SELECT P.id_pre, P.id_lote, P.semana, P.viables, P.estatus, P.fecha_registro, U.nombre_usuario
            FROM PRE_PARASITISMO P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            ORDER BY 
                CASE WHEN P.estatus = 'Pendiente' THEN 1 ELSE 2 END,
                P.id_pre DESC
        """)
        filas = cursor.fetchall()
        
        historial = [] 
        pendientes = 0
        aprobados = 0
        
        meses_es = {"01":"Ene", "02":"Feb", "03":"Mar", "04":"Abr", "05":"May", "06":"Jun", 
                    "07":"Jul", "08":"Ago", "09":"Sep", "10":"Oct", "11":"Nov", "12":"Dic"}

        for f in filas:
            row_dict = dict(f)
            
            # Contadores para KPIs
            if row_dict['estatus'] == 'Pendiente': pendientes += 1
            if row_dict['estatus'] == 'Aprobado': aprobados += 1
            
            # Formateo de fecha
            if row_dict['fecha_registro']:
                try:
                    f_obj = datetime.strptime(row_dict['fecha_registro'][:10], '%Y-%m-%d')
                    hora_str = ""
                    if len(row_dict['fecha_registro']) > 10:
                        hora_obj = datetime.strptime(row_dict['fecha_registro'], '%Y-%m-%d %H:%M:%S')
                        hora_str = hora_obj.strftime(' %I:%M %p')
                    
                    row_dict['fecha_str'] = f"{f_obj.strftime('%d')}-{meses_es[f_obj.strftime('%m')]}-{f_obj.strftime('%Y')}{hora_str}"
                except ValueError:
                    row_dict['fecha_str'] = row_dict['fecha_registro']
                    
            historial.append(row_dict)
            
        conn.close()
    except Exception as e:
        print("Error en Admin Catopar Pre:", e)
        historial = []
        pendientes = aprobados = 0
        
    return render_template('admin/catopar/pre.html', historial=historial, pendientes=pendientes, aprobados=aprobados)

@admin_bp.route('/catopar/pre/revision/<int:id_pre>')
def catopar_pre_revision(id_pre):
    # Esta es la ruta que abre la tarjeta detallada de los 21 garbanzos
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM PRE_PARASITISMO WHERE id_pre = ?", (id_pre,))
        lote = cursor.fetchone()
        
        if not lote:
            flash("El registro solicitado no existe.", "error")
            return redirect(url_for('admin.catopar_pre'))
            
        cursor.execute("SELECT * FROM PRE_PARASITISMO_DETALLE WHERE id_pre = ? ORDER BY num_garbanzo", (id_pre,))
        detalles = cursor.fetchall()
        
        conn.close()
        return render_template('admin/catopar/pre_revision.html', lote=lote, detalles=detalles)
    except Exception as e:
        print("Error en Revisión Pre:", e)
        return redirect(url_for('admin.catopar_pre'))

@admin_bp.route('/catopar/pre/autorizar', methods=['POST'])
def autorizar_pre():
    id_pre = request.form.get('id_pre')
    decision = request.form.get('decision')
    
    estatus_final = 'Aprobado' if decision == 'autorizar' else 'Rechazado'
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE PRE_PARASITISMO SET estatus = ? WHERE id_pre = ?", (estatus_final, id_pre))
        conn.commit()
        
        if estatus_final == 'Aprobado':
            flash('El lote ha sido AUTORIZADO exitosamente.', 'success')
        else:
            flash('El lote ha sido RECHAZADO.', 'error')
            
    except Exception as e:
        flash(f'Error al procesar la autorización: {str(e)}', 'error')
    finally:
        if 'conn' in locals(): conn.close()
        
    return redirect(url_for('admin.catopar_pre'))

@admin_bp.route('/catopar/post')
def catopar_post():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Consulta segura: Usamos LEFT JOIN para evitar que un usuario borrado oculte el lote
        cursor.execute("""
            SELECT 
                C.id_cabecera, C.id_lote, C.fecha_registro, U.nombre_usuario,
                SUM(D.gorg_nacidos) as total_gorg_nacidos,
                SUM(D.gorg_pupas) as total_gorg_pupas,
                SUM(D.cat_negros) as total_cat_negros,
                SUM(D.cat_combinados) as total_cat_combinados,
                SUM(D.cat_ambar) as total_cat_ambar
            FROM POST_PARASITISMO_CABECERA C
            LEFT JOIN USUARIOS U ON C.id_operador = U.id_usuario
            LEFT JOIN POST_PARASITISMO_DETALLE D ON C.id_cabecera = D.id_cabecera
            GROUP BY C.id_cabecera
            ORDER BY C.id_cabecera DESC
        """)
        filas = cursor.fetchall()
        
        historial = []
        total_parasitismo = 0
        total_evaluados = 0
        
        for f in filas:
            row = dict(f) # Convertimos a diccionario para evitar errores de sqlite3.Row
            
            # Sumas seguras con (or 0) por si hay nulos
            t_gorg = (row.get('total_gorg_nacidos') or 0) + (row.get('total_gorg_pupas') or 0)
            t_cat = (row.get('total_cat_negros') or 0) + (row.get('total_cat_combinados') or 0) + (row.get('total_cat_ambar') or 0)
            total_insectos = t_gorg + t_cat
            
            porcentaje = (t_cat / total_insectos * 100) if total_insectos > 0 else 0
            
            # Formateo de fecha seguro
            fecha_str = row.get('fecha_registro', '')
            if fecha_str:
                try:
                    fecha_obj = datetime.strptime(fecha_str[:19], '%Y-%m-%d %H:%M:%S')
                    fecha_str = fecha_obj.strftime('%d/%b/%Y - %I:%M %p')
                except ValueError:
                    try:
                        fecha_obj = datetime.strptime(fecha_str[:10], '%Y-%m-%d')
                        fecha_str = fecha_obj.strftime('%d/%b/%Y')
                    except ValueError:
                        pass
            
            # Armamos el diccionario para el HTML
            historial.append({
                'id_cabecera': row.get('id_cabecera'),
                'id_lote': row.get('id_lote'),
                't_gorg': t_gorg,
                't_cat': t_cat,
                'total_insectos': total_insectos,
                'porcentaje': round(porcentaje, 1),
                'fecha_str': fecha_str,
                'operador': row.get('nombre_usuario') or 'Usuario Desconocido'
            })
            
            total_parasitismo += t_cat
            total_evaluados += total_insectos
            
        promedio_global = round((total_parasitismo / total_evaluados) * 100, 1) if total_evaluados > 0 else 0.0
            
        conn.close()
    except Exception as e:
        print("Error CRÍTICO en Admin Catopar Post:", e)
        historial = []
        promedio_global = 0.0
        
    return render_template('admin/catopar/post.html', historial=historial, promedio_global=promedio_global)

@admin_bp.route('/catopar/post/revision/<int:id_cabecera>')
def catopar_post_revision(id_cabecera):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Obtenemos la cabecera y el nombre del operador
        cursor.execute("""
            SELECT C.*, U.nombre_usuario 
            FROM POST_PARASITISMO_CABECERA C
            JOIN USUARIOS U ON C.id_operador = U.id_usuario
            WHERE C.id_cabecera = ?
        """, (id_cabecera,))
        lote_row = cursor.fetchone()
        
        if not lote_row:
            flash("El registro solicitado no existe.", "error")
            return redirect(url_for('admin.catopar_post'))
            
        lote = dict(lote_row)

        # 2. Obtenemos las 10 unidades de detalle
        cursor.execute("""
            SELECT * FROM POST_PARASITISMO_DETALLE 
            WHERE id_cabecera = ? ORDER BY numero_garbanzo
        """, (id_cabecera,))
        detalles = [dict(row) for row in cursor.fetchall()]

        # 3. Calculamos los totales para las tarjetas inferiores
        totales = {
            'gorgojos': sum(d['gorg_nacidos'] for d in detalles), 
            'completos': sum(d['gorg_pupas'] for d in detalles),
            'negro': sum(d['cat_negros'] for d in detalles),
            'combinado': sum(d['cat_combinados'] for d in detalles),
            'ambar': sum(d['cat_ambar'] for d in detalles)
        }

        conn.close()
        return render_template('admin/catopar/post_revision.html', lote=lote, detalles=detalles, totales=totales)
        
    except Exception as e:
        print("Error en Revisión Post-Parasitismo:", e)
        return redirect(url_for('admin.catopar_post'))
    
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
# ASISTENCIA
# ==========================================


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
# GESTIÓN DE USUARIOS
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
    
    # AGREGAR ESTA LÍNEA AQUÍ
    flash('¡Usuario registrado correctamente!', 'success')
    
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

# ==========================================
# GESTIÓN DE MATERIALES 
# ==========================================
@admin_bp.route('/materiales')
def gestionar_materiales():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Consultamos los materiales uniendo la tabla de áreas
        cursor.execute("""
            SELECT M.id_material, M.nombre_material, M.presentacion, A.nombre_area 
            FROM MATERIALES M
            LEFT JOIN CAT_AREAS A ON M.id_area = A.id_area
            ORDER BY M.id_material DESC
        """)
        materiales = cursor.fetchall()
        
        # Consultamos exclusivamente Chrysopa y Catopar para el selector
        cursor.execute("""
            SELECT id_area, nombre_area FROM CAT_AREAS 
            WHERE nombre_area LIKE '%Chrysopa%' OR nombre_area LIKE '%Catopar%'
        """)
        areas = cursor.fetchall()
        
        conn.close()
    except Exception as e:
        print("Error al cargar materiales:", e)
        materiales = []
        areas = []
        
    return render_template('admin/materiales.html', materiales=materiales, areas=areas)

@admin_bp.route('/materiales/agregar', methods=['POST'])
def agregar_material():
    id_area = request.form.get('id_area')
    nombre_material = request.form.get('nombre_material')
    presentacion = request.form.get('presentacion')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO MATERIALES (id_area, nombre_material, presentacion) 
            VALUES (?, ?, ?)
        """, (id_area, nombre_material, presentacion))
        conn.commit()
        conn.close()
        flash('Material agregado correctamente al catálogo.', 'success')
    except Exception as e:
        flash(f'Error al agregar material: {str(e)}', 'error')
        
    return redirect(url_for('admin.gestionar_materiales'))

@admin_bp.route('/materiales/eliminar/<int:id_material>', methods=['POST'])
def eliminar_material(id_material):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM MATERIALES WHERE id_material = ?", (id_material,))
        conn.commit()
        conn.close()
        flash('Material eliminado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar material: {str(e)}', 'error')
        
    return redirect(url_for('admin.gestionar_materiales'))