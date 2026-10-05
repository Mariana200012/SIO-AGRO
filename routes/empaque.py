from flask import Blueprint, render_template, request, flash, redirect, url_for
from database import get_db_connection

# Creamos el Blueprint para el módulo de Empaque
empaque_bp = Blueprint('empaque', __name__, url_prefix='/empaque')

@empaque_bp.route('/dashboard', methods=['GET'])
def dashboard_empaque():
    """Renderiza el panel general de control de empaque y producto terminado."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Aquí puedes consultar métricas recientes de empaque si lo requieres
    # cursor.execute("SELECT * FROM EMPAQUE_REGISTROS ORDER BY fecha_hora DESC LIMIT 10")
    # registros = cursor.fetchall()
    
    conn.close()
    
    # Flask buscará este archivo en templates/empaque/dashboard.html
    return render_template('empaque/dashboard.html')

@empaque_bp.route('/registrar', methods=['POST'])
def registrar_empaque():
    """Registra un nuevo lote empacado y valida el NIP del operador."""
    lote_id = request.form.get('lote_id')
    cantidad_cajas = request.form.get('cantidad_cajas')
    calidad = request.form.get('calidad') # 'OPTIMA', 'REVISION', etc.
    nip = request.form.get('nip')
    
    if not lote_id or not nip:
        flash('El ID de lote y la firma NIP son obligatorios.', 'error')
        return redirect(url_for('empaque.dashboard_empaque'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # CORRECCIÓN: La columna en tu BD se llama nip_firma, no nip
        cursor.execute("SELECT id_usuario FROM USUARIOS WHERE nip_firma = ?", (nip,))
        operador = cursor.fetchone()
        
        if not operador:
            flash('Firma NIP no válida para empaque. Acceso denegado.', 'error')
            return redirect(url_for('empaque.dashboard_empaque'))
            
        id_operador = operador['id_usuario']
        
        # Guardar el registro de empaque en la base de datos
        # (Asegúrate de tener la tabla EMPAQUE_REGISTROS o cámbiala por EMP_LOTE según tu BD)
        cursor.execute('''
            INSERT INTO EMPAQUE_REGISTROS (id_lote, cantidad_cajas, calidad, id_operador, fecha_hora)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (lote_id, cantidad_cajas, calidad, id_operador))
        
        conn.commit()
        flash('¡Lote empacado registrado exitosamente!', 'success')
        
    except Exception as e:
        flash(f'Error al registrar empaque: {e}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('empaque.dashboard_empaque'))

@empaque_bp.route('/inventario', methods=['GET'])
def inventario():
    # Después conectaremos esto con SQLite

    return render_template('empaque/inventario.html')

@empaque_bp.route('/inventario')
def inventario_empaque():
    # Esta ruta cargará la pantalla de Entradas / Salidas
    return render_template('empaque/inventario.html')

@empaque_bp.route('/historial')
def historial_empaque():
    # Esta ruta cargará la bitácora de movimientos
    return render_template('empaque/historial.html')