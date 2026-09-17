from flask import Blueprint, render_template, request, redirect, url_for
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
    conexion = sqlite3.connect('Bd_SIO-AGRO.db')
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    
    cursor.execute("SELECT * FROM USUARIOS")
    lista_usuarios = cursor.fetchall()
    conexion.close()
    
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
    conexion = sqlite3.connect('Bd_SIO-AGRO.db')
    cursor = conexion.cursor()
    
    cursor.execute("DELETE FROM USUARIOS WHERE id_usuario = ?", (id_usuario,))
    conexion.commit()
    conexion.close()
    
    return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/editar/<int:id_usuario>', methods=['POST'])
def editar_usuario(id_usuario):
    # Recibimos los nuevos datos
    nombre = request.form['nombre_usuario']
    puesto = request.form['puesto']
    nip = request.form['nip_firma']
    id_area = request.form['id_area']
    
    # Actualizamos la base de datos
    conexion = sqlite3.connect('Bd_SIO-AGRO.db')
    cursor = conexion.cursor()
    cursor.execute(
        """UPDATE USUARIOS 
           SET id_area = ?, nombre_usuario = ?, puesto = ?, nip_firma = ? 
           WHERE id_usuario = ?""",
        (id_area, nombre, puesto, nip, id_usuario)
    )
    conexion.commit()
    conexion.close()
    
    return redirect(url_for('admin.usuarios'))