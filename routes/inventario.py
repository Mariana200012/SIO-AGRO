from flask import Blueprint, render_template, request, flash, redirect, url_for
from database import get_db_connection

# Creamos el Blueprint para el módulo de Inventario / Almacén
inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')

@inventario_bp.route('/solicitudes', methods=['GET'])
def listar_solicitudes():
    """Renderiza el panel del encargado de almacén con las solicitudes agrupadas por área."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Aquí consultarías los tickets pendientes en tu base de datos SQLite
    # Ejemplo: cursor.execute("SELECT * FROM SOLICITUD_MATERIALES WHERE estatus = 'PENDIENTE'")
    # solicitudes = cursor.fetchall()
    
    conn.close()
    
    # Renderiza la vista que organizamos en templates/inventario/solicitudes.html
    return render_template('inventario/solicitudes.html')

@inventario_bp.route('/solicitudes/surtir/<int:folio>', methods=['POST'])
def autorizar_surtido(folio):
    """Procesa la autorización de un ticket, descontando los insumos del stock general."""
    nip_almacen = request.form.get('nip')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Validar identidad del encargado de almacén
        cursor.execute("SELECT id_usuario FROM USUARIOS WHERE nip = ?", (nip_almacen,))
        almacenista = cursor.fetchone()
        
        if not almacenista:
            flash('NIP de almacén incorrecto. Autorización denegada.', 'error')
            return redirect(url_for('inventario.listar_solicitudes'))
            
        # 2. Transacción de Surtido: Descontar stock y actualizar estatus del ticket
        # (Aquí realizarías los UPDATE a tu tabla de inventario y el UPDATE de estatus a 'SURTIDO')
        
        conn.commit()
        flash(f'Ticket #{folio} autorizado y surtido correctamente. Stock actualizado.', 'success')
        
    except Exception as e:
        flash(f'Error al procesar el surtido: {e}', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('inventario.listar_solicitudes'))

@inventario_bp.route('/entradas', methods=['GET', 'POST'])
def registrar_compras():
    """Permite registrar la entrada de nuevas compras o reabastecimiento al almacén."""
    if request.method == 'POST':
        insumo = request.form.get('insumo')
        cantidad = request.form.get('cantidad')
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Sumar al stock actual o registrar entrada
            cursor.execute('''
                INSERT INTO INV_HISTORIAL (tipo_movimiento, insumo, cantidad, fecha)
                VALUES ('ENTRADA', ?, ?, CURRENT_TIMESTAMP)
            ''', (insumo, cantidad))
            
            conn.commit()
            flash('Entrada de inventario registrada con éxito.', 'success')
        except Exception as e:
            flash(f'Error al registrar entrada: {e}', 'error')
        finally:
            conn.close()
            
        return redirect(url_for('inventario.registrar_compras'))
        
    return render_template('inventario/entradas.html')