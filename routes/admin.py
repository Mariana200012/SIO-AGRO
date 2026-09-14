from flask import Blueprint, render_template

# Declaramos el blueprint que app.py está buscando
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
def dashboard():
    return "Aquí irá el panel de control del Administrador"

# --- NUEVAS RUTAS EXCLUSIVAS DEL ADMINISTRADOR ---

@admin_bp.route('/ocupacion')
def ocupacion():
    # Asegúrate de tener o crear este archivo en templates/admin/chrysopa.html
    return render_template('admin/chrysopa/ocupacion.html')

@admin_bp.route('/pre')
def pre():
    # Asegúrate de tener o crear este archivo en templates/admin/catopar.html
    return render_template('admin/catopar/pre.html')

# --- ESTO ES LO ÚNICO QUE AGREGAMOS PARA QUE FUNCIONEN TUS OTROS BOTONES ---

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