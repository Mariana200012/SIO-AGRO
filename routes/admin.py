from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import sqlite3
import pandas as pd
from flask import send_file
import io
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Declaramos el blueprint principal del Administrador
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ==========================================
# FUNCIÓN VITAL: CONEXIÓN A LA BASE DE DATOS
# ==========================================
def get_db_connection():
    conn = sqlite3.connect('Bd_SIO-AGRO.db', isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn
# ==========================================
# DASHBOARD PRINCIPAL Y REDIRECCIÓN INICIAL
# ==========================================
@admin_bp.route('/metricas')
def metricas():
    return redirect(url_for('admin.dashb_chrysopa'))

@admin_bp.route('/metricas/chrysopa')
def dashb_chrysopa():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM PROD_DETALLE_CHRYSOPA")
    total_lotes = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(cantidad) FROM OCUPACION")
    total_ocupacion = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(cantidad) FROM PUPACION")
    total_pupacion = cursor.fetchone()[0] or 0
    
    conn.close()

    chrysopa_data = [int(total_ocupacion), int(total_pupacion)]

    return render_template(
        'admin/dashb_chrysopa.html',
        total_lotes=total_lotes,
        total_ocupacion=total_ocupacion,
        total_pupacion=total_pupacion,
        chrysopa_data=chrysopa_data
    )

@admin_bp.route('/metricas/catopar')
def dashb_catopar():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id_lote, promedio_grandes, estatus 
        FROM PRE_PARASITISMO 
        ORDER BY id_pre DESC LIMIT 6
    """)
    lotes_pre = cursor.fetchall()
    
    cursor.execute("""
        SELECT 
            SUM(D.gorg_nacidos) as total_gorg_nac,
            SUM(D.gorg_pupas) as total_gorg_pup,
            SUM(D.cat_negros) as total_cat_neg,
            SUM(D.cat_combinados) as total_cat_com,
            SUM(D.cat_ambar) as total_cat_amb
        FROM POST_PARASITISMO_DETALLE D
    """)
    post_totales = cursor.fetchone()
    
    conn.close()
    
    pre_lotes = [row['id_lote'] for row in lotes_pre][::-1]
    pre_promedios = [row['promedio_grandes'] for row in lotes_pre][::-1]
    
    post_data = [
        post_totales['total_cat_neg'] or 0,
        post_totales['total_cat_amb'] or 0,
        post_totales['total_gorg_nac'] or 0,
        post_totales['total_gorg_pup'] or 0
    ] if post_totales else [0, 0, 0, 0]

    return render_template(
        'admin/dashb_catopar.html',
        pre_lotes=pre_lotes,
        pre_promedios=pre_promedios,
        post_data=post_data
    )

# ==========================================
# MÓDULO CHRYSOPA
# ==========================================
@admin_bp.route('/ocupacion')
def ocupacion():
    termino_busqueda = request.args.get('buscar', '').strip()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT P.id_detallechr, P.id_lote, P.semana, P.fecha_registro, U.nombre_usuario
            FROM PROD_DETALLE_CHRYSOPA P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            WHERE P.id_detallechr IN (SELECT DISTINCT id_detallechr FROM OCUPACION)
        """
        parametros = []
        
        if termino_busqueda:
            query += " AND P.id_lote LIKE ?"
            parametros.append(f"%{termino_busqueda}%")
            
        query += " ORDER BY P.id_detallechr DESC LIMIT 30"
        
        cursor.execute(query, parametros)
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
        print("Error en admin ocupacion:", e)
        historial = []; promedio_global = 0.0

    return render_template('admin/chrysopa/ocupacion.html', historial=historial, promedio_global=promedio_global)

@admin_bp.route('/pupacion')
def pupacion():
    termino_busqueda = request.args.get('buscar', '').strip()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT P.id_detallechr, P.id_lote, P.semana, P.fecha_registro, U.nombre_usuario
            FROM PROD_DETALLE_CHRYSOPA P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            WHERE P.id_detallechr IN (SELECT DISTINCT id_detallechr FROM PUPACION)
        """
        parametros = []
        
        if termino_busqueda:
            query += " AND P.id_lote LIKE ?"
            parametros.append(f"%{termino_busqueda}%")
            
        query += " ORDER BY P.id_detallechr DESC LIMIT 30"
        
        cursor.execute(query, parametros)
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
        print("Error en admin pupacion:", e)
        historial = []; promedio_global = 0.0

    return render_template('admin/chrysopa/pupacion.html', historial=historial, promedio_global=promedio_global)


# =====================================================================
# MÓDULO CATOPAR (ADMIN) - INICIA SIEMPRE EN PRE
# =====================================================================
@admin_bp.route('/catopar')
def catopar_index():
    return redirect(url_for('admin.catopar_pre'))

@admin_bp.route('/catopar/pre')
def catopar_pre():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT P.*, U.nombre_usuario 
            FROM PRE_PARASITISMO P
            JOIN USUARIOS U ON P.id_operador = U.id_usuario
            ORDER BY P.id_pre DESC LIMIT 30
        """)
        filas = cursor.fetchall()
        
        historial = []
        pendientes = 0
        aprobados = 0
        
        for f in filas:
            row = dict(f)
            
            if row.get('estatus') == 'Pendiente':
                pendientes += 1
            elif row.get('estatus') == 'Aprobado':
                aprobados += 1
                
            fecha_str = row.get('fecha_registro', '')
            if fecha_str:
                try:
                    fecha_obj = datetime.strptime(fecha_str[:19], '%Y-%m-%d %H:%M:%S')
                    fecha_str = fecha_obj.strftime('%d/%b/%Y - %I:%M %p')
                except ValueError:
                    pass
                    
            row['fecha_str'] = fecha_str
            historial.append(row)
            
        conn.close()
        return render_template('admin/catopar/pre.html', historial=historial, pendientes=pendientes, aprobados=aprobados)
        
    except Exception as e:
        print("Error en Admin Pre-Parasitismo:", e)
        return render_template('admin/catopar/pre.html', historial=[], pendientes=0, aprobados=0)

@admin_bp.route('/catopar/pre/revision/<int:id_pre>')
def catopar_pre_revision(id_pre):
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
        
        # Consultamos agrupando por cabecera y sumando los valores del detalle
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
            LIMIT 30
        """)
        filas = cursor.fetchall()
        
        historial = []
        total_parasitismo = 0
        total_evaluados = 0
        
        for f in filas:
            row = dict(f) 
            
            t_gorg_nac = row.get('total_gorg_nacidos') or 0
            t_gorg_pup = row.get('total_gorg_pupas') or 0
            t_cat_neg = row.get('total_cat_negros') or 0
            t_cat_com = row.get('total_cat_combinados') or 0
            t_cat_amb = row.get('total_cat_ambar') or 0

            # SUMA TOTAL DE GORGORJOS (Nacidos + Pupas)
            t_gorg = t_gorg_nac + t_gorg_pup
            
            # SUMA TOTAL DE CATOPAS (Negros + Combinados + Ámbar)
            t_cat = t_cat_neg + t_cat_com + t_cat_amb
            
            total_insectos = t_gorg + t_cat
            porcentaje = (t_cat / total_insectos * 100) if total_insectos > 0 else 0
            
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
            
            historial.append({
                'id_cabecera': row.get('id_cabecera'),
                'id_lote': row.get('id_lote'),
                't_gorg': t_gorg,   # <--- Ahora muestra la suma numérica total
                't_cat': t_cat,     # <--- Ahora muestra la suma numérica total
                'total_insectos': total_insectos,
                'porcentaje': round(porcentaje, 1),
                'fecha_str': fecha_str if fecha_str else '--',
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

        cursor.execute("""
            SELECT * FROM POST_PARASITISMO_DETALLE 
            WHERE id_cabecera = ? ORDER BY numero_garbanzo
        """, (id_cabecera,))
        
        detalles = []
        for row in cursor.fetchall():
            d = dict(row)
            suma_cat = (d.get('cat_negros') or 0) + (d.get('cat_combinados') or 0) + (d.get('cat_ambar') or 0)
            total_fila = (d.get('gorg_nacidos') or 0) + (d.get('gorg_pupas') or 0) + suma_cat
            porcentaje_ind = (suma_cat / total_fila * 100) if total_fila > 0 else 0.0
            
            d['porcentaje_individual'] = round(porcentaje_ind, 1)
            detalles.append(d)

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
    flash('¡Usuario registrado correctamente!', 'success')
    return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/eliminar/<int:id_usuario>', methods=['POST'])
def eliminar_usuario(id_usuario):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE USUARIOS SET estatus = 'Inactivo' WHERE id_usuario = ?", (id_usuario,))
        conn.commit()
        flash('Operador dado de baja correctamente.', 'success')
    except Exception as e:
        flash(f'Error al dar de baja: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin.usuarios'))

# ==========================================
# FORMATO TABLA PARA EXPORTAR EXCEL 
# ==========================================
# Función auxiliar para aplicar bordes negros definidos a la tabla
def aplicar_estilo_tabla(writer, sheet_name, df, titulo=""):
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    
    # Fuentes limpias y profesionales
    font_titulo = Font(name='Segoe UI', size=13, bold=True, color='1E293B')
    font_header = Font(name='Segoe UI', size=10, bold=True, color='000000')
    font_body = Font(name='Segoe UI', size=10, color='334155')
    
    # Bordes NEGROS y delgados para cada celda
    borde_negro = Border(
        left=Side(style='thin', color='000000'),
        right=Side(style='thin', color='000000'),
        top=Side(style='thin', color='000000'),
        bottom=Side(style='thin', color='000000')
    )
    
    # Si hay título, lo insertamos en la fila 1
    start_row = 1
    if titulo:
        worksheet.insert_rows(1, 2)
        worksheet.cell(row=1, column=1, value=titulo).font = font_titulo
        start_row = 3
        
    # Aplicar formato y bordes negros a las cabeceras
    for col_num in range(1, len(df.columns) + 1):
        cell = worksheet.cell(row=start_row, column=col_num)
        cell.font = font_header
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = borde_negro

    # Aplicar bordes negros a todas las filas de datos
    for row in worksheet.iter_rows(min_row=start_row + 1, max_row=start_row + len(df), min_col=1, max_col=len(df.columns)):
        for cell in row:
            cell.font = font_body
            cell.border = borde_negro
            cell.alignment = Alignment(horizontal='center', vertical='center')

    # Auto-ajustar el ancho de las columnas
    for col in worksheet.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        worksheet.column_dimensions[col_letter].width = max(max_len + 4, 15)

# 1. EXCEL PARA PRE-PARASITISMO (Con Promedio G y formato de tabla)
@admin_bp.route('/catopar/pre/exportar/<int:id_pre>')
def exportar_pre_excel(id_pre):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT C.*, U.nombre_usuario 
            FROM PRE_PARASITISMO C 
            LEFT JOIN USUARIOS U ON C.id_operador = U.id_usuario 
            WHERE C.id_pre = ?
        """, (id_pre,))
        lote_row = cursor.fetchone()
        
        cursor.execute("SELECT * FROM PRE_PARASITISMO_DETALLE WHERE id_pre = ? ORDER BY num_garbanzo", (id_pre,))
        detalles_rows = cursor.fetchall()
        conn.close()
        
        if not lote_row:
            return "Lote no encontrado", 404
            
        lote = dict(lote_row)
        
        data = []
        for d in detalles_rows:
            row = dict(d)
            data.append({
                "Garbanzo #": row.get('num_garbanzo'),
                "Chicas (CH)": row.get('chicas', 0),
                "Medianas (M)": row.get('medianas', 0),
                "Grandes (G)": row.get('grandes', 0),
                "Pupas (P)": row.get('pupas', 0) if row.get('pupas') is not None else 0
            })
            
        df_detalle = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja de Resumen incluyendo el Promedio G
            resumen_data = {
                "Parámetro": ["ID Lote", "Semana Operativa", "Operador", "Fecha de Captura", "Estatus", "Total Viables", "Promedio G"],
                "Valor": [
                    str(lote.get('id_lote', '')),
                    str(lote.get('semana', '')),
                    str(lote.get('nombre_usuario', 'Desconocido')),
                    str(lote.get('fecha_registro', '')),
                    str(lote.get('estatus', '')),
                    str(lote.get('viables', '')),
                    str(lote.get('promedio_grandes', '0.0'))
                ]
            }
            df_resumen = pd.DataFrame(resumen_data)
            
            df_resumen.to_excel(writer, sheet_name='Resumen Lote', index=False)
            df_detalle.to_excel(writer, sheet_name='Detalle 21 Unidades', index=False)
            
            # Aplicar estilos de tablas con líneas
            aplicar_estilo_tabla(writer, 'Resumen Lote', df_resumen, "Resumen General del Lote")
            aplicar_estilo_tabla(writer, 'Detalle 21 Unidades', df_detalle, "Desglose por Garbanzo (21 Unidades)")
            
        output.seek(0)
        # Nombre personalizado con Catopar y Pre
        filename = f"Catopar_Pre_Lote_{lote.get('id_lote', id_pre)}.xlsx"
        
        return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error detallado al generar Excel: {str(e)}", 500


# 2. EXCEL PARA POST-PARASITISMO (Con formato de tabla con líneas)
@admin_bp.route('/catopar/post/exportar/<int:id_cabecera>')
def exportar_post_excel(id_cabecera):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT C.*, U.nombre_usuario FROM POST_PARASITISMO_CABECERA C LEFT JOIN USUARIOS U ON C.id_operador = U.id_usuario WHERE C.id_cabecera = ?", (id_cabecera,))
        lote_row = cursor.fetchone()
        
        cursor.execute("SELECT * FROM POST_PARASITISMO_DETALLE WHERE id_cabecera = ? ORDER BY numero_garbanzo", (id_cabecera,))
        detalles_rows = cursor.fetchall()
        conn.close()
        
        if not lote_row:
            return "Lote no encontrado", 404
            
        lote = dict(lote_row)
        
        data = []
        tot_cat_global = 0
        tot_ins_global = 0
        
        for d in detalles_rows:
            row = dict(d)
            gorg = row.get('gorg_nacidos', 0) or 0
            comp = row.get('gorg_pupas', 0) or 0
            neg = row.get('cat_negros', 0) or 0
            comb = row.get('cat_combinados', 0) or 0
            amb = row.get('cat_ambar', 0) or 0
            
            tot_cat = neg + comb + amb
            tot_ins = gorg + comp + tot_cat
            
            tot_cat_global += tot_cat
            tot_ins_global += tot_ins
            
            porcentaje = round((tot_cat / tot_ins * 100), 1) if tot_ins > 0 else 0.0
            
            data.append({
                "Unidad #": row.get('numero_garbanzo', 1),
                "Gorgojos": gorg,
                "Completos": comp,
                "Negro": neg,
                "Combinado": comb,
                "Ámbar": amb,
                "Efectividad (%)": f"{porcentaje}%"
            })
            
        efectividad_global = round((tot_cat_global / tot_ins_global * 100), 1) if tot_ins_global > 0 else 0.0
        
        df_detalle = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resumen_data = {
                "Parámetro": ["ID Lote", "Operador", "Fecha de Captura", "Efectividad Global"],
                "Valor": [
                    str(lote.get('id_lote', '')),
                    str(lote.get('nombre_usuario', 'Desconocido')),
                    str(lote.get('fecha_registro', '')),
                    f"{efectividad_global}%"
                ]
            }
            df_resumen = pd.DataFrame(resumen_data)
            
            df_resumen.to_excel(writer, sheet_name='Resumen Lote', index=False)
            df_detalle.to_excel(writer, sheet_name='Detalle 10 Unidades', index=False)
            
            aplicar_estilo_tabla(writer, 'Resumen Lote', df_resumen, "Resumen General Post-Parasitismo")
            aplicar_estilo_tabla(writer, 'Detalle 10 Unidades', df_detalle, "Desglose por Unidad (10 Garbanzos)")
            
        output.seek(0)
        # Nombre personalizado con Catopar y Post
        filename = f"Catopar_Post_Lote_{lote.get('id_lote', id_cabecera)}.xlsx"
        
        return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error detallado al generar Excel: {str(e)}", 500