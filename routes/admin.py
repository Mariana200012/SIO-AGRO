from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3

# Declaramos el blueprint principal del Administrador
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ==========================================
# 1. PANEL PRINCIPAL (DASHBOARD)
# ==========================================
@admin_bp.route('/dashboard')
def dashboard():
    # AQUÍ ESTÁ EL ARREGLO: Ya te regresa a tu vista principal con las 3 tarjetas
    return render_template('index.html')


# ==========================================
# 2. MÓDULO CHRYSOPA
# ==========================================
@admin_bp.route('/ocupacion')
def ocupacion():
    return render_template('admin/chrysopa/ocupacion.html')

@admin_bp.route('/pupacion')
def pupacion():
    return render_template('admin/chrysopa/pupacion.html')

@admin_bp.route('/eclosion')
def eclosion():
    return render_template('admin/chrysopa/eclosion.html')

@admin_bp.route('/mortalidad')
def mortalidad():
    return render_template('admin/chrysopa/mortalidad.html')

@admin_bp.route('/fallas')
def fallas():
    return render_template('admin/chrysopa/fallas.html')


# ==========================================
# 3. MÓDULO CATOPAR
# ==========================================
@admin_bp.route('/pre')
def pre():
    return render_template('admin/catopar/pre.html')

@admin_bp.route('/post')
def post():
    return render_template('admin/catopar/post.html')


# ==========================================
# 4. GESTIÓN DE USUARIOS (Conexión a SQLite)
# ==========================================
@admin_bp.route('/usuarios')
def usuarios():
    conn = sqlite3.connect('Bd_SIO-AGRO.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # EL TRUCO: Solo traemos a los que dicen 'Activo'
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
    
    conexion = sqlite3.connect('Bd_SIO-AGRO.db')
    cursor = conexion.cursor()
    
    # Insertamos sin enviar el id_usuario, SQLite se encarga del Autoincremento
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
        conn = sqlite3.connect('Bd_SIO-AGRO.db', isolation_level=None)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Revisar si el usuario a desactivar es Administrador
        cursor.execute("SELECT id_area FROM USUARIOS WHERE id_usuario = ?", (id_usuario,))
        usuario = cursor.fetchone()

        if usuario and str(usuario['id_area']).strip() == '5':
            # Contar administradores que sigan ACTIVOS
            cursor.execute("SELECT COUNT(*) as total FROM USUARIOS WHERE (id_area = 5 OR id_area = '5') AND estatus = 'Activo'")
            total_admins = cursor.fetchone()['total']

            if total_admins <= 1:
                flash('Acción denegada: No puedes dar de baja al único Administrador.', 'error')
                return redirect(url_for('admin.usuarios'))

        # EN LUGAR DE BORRAR, LO PASAMOS A INACTIVO
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
        conn = sqlite3.connect('Bd_SIO-AGRO.db', isolation_level=None)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF;")

        # 1. Obtener datos actuales del usuario ANTES de hacer cualquier cosa
        cursor.execute("SELECT id_area, puesto, estatus FROM USUARIOS WHERE id_usuario = ?", (id_usuario,))
        usuario_actual = cursor.fetchone()
        
        if not usuario_actual:
            return redirect(url_for('admin.usuarios'))
            
        area_actual = str(usuario_actual['id_area']).strip()
        
        # Rescate de datos (por si el HTML no los envía)
        nuevo_id_area = str(nuevo_id_area).strip() if nuevo_id_area else area_actual
        puesto_nuevo = str(puesto_nuevo).strip() if puesto_nuevo else str(usuario_actual['puesto']).strip()

        # 2. REGLA INQUEBRANTABLE PARA EL ÚNICO ADMINISTRADOR ACTIVO
        # Si el usuario que están editando actualmente es Admin (5) y está Activo...
        if area_actual == '5' and usuario_actual['estatus'] == 'Activo':
            
            # Y está intentando dejar de ser Admin (cambiando su Puesto o su Área)
            if nuevo_id_area != '5' or puesto_nuevo.lower() != 'administrador':
                
                # Contamos cuántos administradores ACTIVOS quedan en total
                cursor.execute("SELECT COUNT(*) as total FROM USUARIOS WHERE CAST(id_area AS TEXT) = '5' AND estatus = 'Activo'")
                total_admins = cursor.fetchone()['total']
                
                # Si es el último, lo bloqueamos inmediatamente
                if total_admins <= 1:
                    flash('Acción denegada: Eres el único Administrador activo. No puedes cambiar tu Puesto ni tu Área.', 'error')
                    return redirect(url_for('admin.usuarios'))

        # 3. Guardar cambios en la base de datos (si pasó la validación)
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