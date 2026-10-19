from flask import Blueprint, render_template, request, flash, redirect, url_for
from database import get_db_connection
from datetime import datetime, timedelta

empaque_bp = Blueprint('empaque', __name__, url_prefix='/empaque')

# =====================================================================
# 1. DASHBOARD (Control de Lotes y FIFO)
# =====================================================================
@empaque_bp.route('/dashboard')
def dashboard_empaque():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Obtener Stock Total
    cursor.execute("SELECT SUM(cantidad_disponible) as total FROM EMP_INVENTARIO_HUEVO WHERE estatus = 'Disponible'")
    stock_total = cursor.fetchone()['total'] or 0

    # 2. Obtener lotes disponibles ordenados por fecha de ingreso (FIFO)
    cursor.execute("""
        SELECT id_recepcion, fecha_ingreso, fecha_caducidad, cantidad_disponible 
        FROM EMP_INVENTARIO_HUEVO 
        WHERE estatus = 'Disponible' 
        ORDER BY fecha_ingreso ASC
    """)
    lotes_fifo = cursor.fetchall()

    # 3. Calcular riesgos de caducidad (Ej: huevo que caduca en menos de 2 días)
    fechas_riesgo = 0
    fechas_sanas = 0
    hoy = datetime.now()

    lotes_procesados = []
    for lote in lotes_fifo:
        caducidad = datetime.strptime(lote['fecha_caducidad'], '%Y-%m-%d %H:%M:%S')
        dias_restantes = (caducidad - hoy).days
        
        estado = "SANO"
        if dias_restantes <= 2:
            fechas_riesgo += 1
            estado = "RIESGO"
        else:
            fechas_sanas += 1

        lotes_procesados.append({
            'fecha_ingreso': datetime.strptime(lote['fecha_ingreso'], '%Y-%m-%d %H:%M:%S').strftime('%d/%b'),
            'cantidad': lote['cantidad_disponible'],
            'dias_restantes': dias_restantes,
            'estado': estado
        })

    conn.close()
    
    return render_template('empaque/dashboard.html', 
                           stock_total=stock_total, 
                           fechas_riesgo=fechas_riesgo, 
                           fechas_sanas=fechas_sanas, 
                           lotes_fifo=lotes_procesados)

# =====================================================================
# 2. INVENTARIO (Ingresar y Retirar)
# =====================================================================
@empaque_bp.route('/inventario')
def inventario_empaque():
    return render_template('empaque/inventario.html')

@empaque_bp.route('/inventario/ingreso', methods=['POST'])
def ingresar_huevo():
    cantidad = float(request.form.get('cantidad'))
    nip = request.form.get('nip')
    dias_caducidad = 12 
    
    fecha_actual = datetime.now()
    fecha_caducidad = fecha_actual + timedelta(days=dias_caducidad)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id_usuario FROM USUARIOS WHERE nip_firma = ? AND estatus = 'Activo'", (nip,))
        operador = cursor.fetchone()
        if not operador:
            flash('NIP Incorrecto.', 'error')
            return redirect(url_for('empaque.inventario_empaque'))
            
        # Insertar el nuevo lote
        cursor.execute("""
            INSERT INTO EMP_INVENTARIO_HUEVO (fecha_ingreso, fecha_caducidad, cantidad_inicial, cantidad_disponible, id_operador)
            VALUES (?, ?, ?, ?, ?)
        """, (fecha_actual.strftime('%Y-%m-%d %H:%M:%S'), fecha_caducidad.strftime('%Y-%m-%d %H:%M:%S'), cantidad, cantidad, operador['id_usuario']))
        
        id_recepcion = cursor.lastrowid

        # Guardar en bitácora
        cursor.execute("""
            INSERT INTO EMP_HISTORIAL_HUEVO (id_recepcion, tipo_movimiento, cantidad, fecha_movimiento, id_operador)
            VALUES (?, 'ENTRADA', ?, ?, ?)
        """, (id_recepcion, cantidad, fecha_actual.strftime('%Y-%m-%d %H:%M:%S'), operador['id_usuario']))
        
        conn.commit()
        flash(f'Ingreso registrado. Caduca el {fecha_caducidad.strftime("%d/%m/%Y")}.', 'success')
        
    except Exception as e:
        flash(f'Error al registrar: {str(e)}', 'error')
    finally:
        if 'conn' in locals(): conn.close()
        
    return redirect(url_for('empaque.inventario_empaque'))

@empaque_bp.route('/inventario/retiro', methods=['POST'])
def retirar_huevo():
    cantidad_a_retirar = float(request.form.get('cantidad'))
    nip = request.form.get('nip')
    fecha_mov = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id_usuario FROM USUARIOS WHERE nip_firma = ? AND estatus = 'Activo'", (nip,))
        operador = cursor.fetchone()
        if not operador:
            flash('NIP Incorrecto.', 'error')
            return redirect(url_for('empaque.inventario_empaque'))

        # LÓGICA FIFO: Buscar los lotes más viejos que aún tengan huevo
        cursor.execute("SELECT id_recepcion, cantidad_disponible FROM EMP_INVENTARIO_HUEVO WHERE estatus = 'Disponible' ORDER BY fecha_ingreso ASC")
        lotes = cursor.fetchall()

        cantidad_restante_por_retirar = cantidad_a_retirar

        for lote in lotes:
            if cantidad_restante_por_retirar <= 0:
                break
                
            disponible_en_lote = lote['cantidad_disponible']
            id_lote = lote['id_recepcion']

            if disponible_en_lote <= cantidad_restante_por_retirar:
                # Nos acabamos todo este lote
                descontar = disponible_en_lote
                nuevo_estado = 'Agotado'
                nueva_cantidad = 0
            else:
                # Solo tomamos una parte de este lote
                descontar = cantidad_restante_por_retirar
                nuevo_estado = 'Disponible'
                nueva_cantidad = disponible_en_lote - descontar

            # Actualizar el lote
            cursor.execute("UPDATE EMP_INVENTARIO_HUEVO SET cantidad_disponible = ?, estatus = ? WHERE id_recepcion = ?", (nueva_cantidad, nuevo_estado, id_lote))
            
            # Registrar el movimiento de este pedazo en el historial
            cursor.execute("""
                INSERT INTO EMP_HISTORIAL_HUEVO (id_recepcion, tipo_movimiento, cantidad, fecha_movimiento, id_operador)
                VALUES (?, 'SALIDA', ?, ?, ?)
            """, (id_lote, descontar, fecha_mov, operador['id_usuario']))

            cantidad_restante_por_retirar -= descontar

        if cantidad_restante_por_retirar > 0:
            conn.rollback()
            flash('No hay suficiente stock en el cuarto frío para retirar esa cantidad.', 'error')
        else:
            conn.commit()
            flash('Retiro de huevo completado bajo sistema FIFO.', 'success')

    except Exception as e:
        if 'conn' in locals(): conn.rollback()
        flash(f'Error: {str(e)}', 'error')
    finally:
        if 'conn' in locals(): conn.close()

    return redirect(url_for('empaque.inventario_empaque'))

# =====================================================================
# 3. HISTORIAL (Bitácora)
# =====================================================================
@empaque_bp.route('/historial')
def historial_empaque():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Unimos el historial con el inventario (para saber de qué fecha era el huevo) y con el usuario
    cursor.execute("""
        SELECT H.tipo_movimiento, H.cantidad, H.fecha_movimiento, 
               I.fecha_ingreso as fecha_lote_afectado, U.nombre_usuario 
        FROM EMP_HISTORIAL_HUEVO H
        JOIN EMP_INVENTARIO_HUEVO I ON H.id_recepcion = I.id_recepcion
        JOIN USUARIOS U ON H.id_operador = U.id_usuario
        ORDER BY H.fecha_movimiento DESC
        LIMIT 50
    """)
    movimientos_crud = cursor.fetchall()
    
    movimientos = []
    for mov in movimientos_crud:
        f_mov = datetime.strptime(mov['fecha_movimiento'], '%Y-%m-%d %H:%M:%S')
        f_lote = datetime.strptime(mov['fecha_lote_afectado'], '%Y-%m-%d %H:%M:%S')
        
        movimientos.append({
            'tipo': mov['tipo_movimiento'],
            'cantidad': mov['cantidad'],
            'fecha_lote': f_lote.strftime('%d/%b/%Y'),
            'operador': mov['nombre_usuario'],
            'fecha_op': f_mov.strftime('%d/%b/%Y - %H:%M hrs')
        })
        
    conn.close()
    
    return render_template('empaque/historial.html', movimientos=movimientos)