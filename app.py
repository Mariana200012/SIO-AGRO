from flask import Flask, redirect, url_for, render_template, session
from routes.asistencia import asistencia_bp
#from database import init_db

# Importamos todos los blueprints desde la carpeta routes
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.empaque import empaque_bp
from routes.inventario import inventario_bp
from routes.prod_chrysopa import prod_chrysopa_bp
from routes.prod_catopar import prod_catopar_bp


app = Flask(__name__)
app.secret_key = 'clave_secreta_koppert'

# Inicializa la BD si no existe
#init_db()

# Registramos los Blueprints en la aplicación
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(empaque_bp)
app.register_blueprint(inventario_bp)
app.register_blueprint(prod_chrysopa_bp)
app.register_blueprint(prod_catopar_bp)
app.register_blueprint(asistencia_bp)

@app.route('/')
def base_route():
    """Ruta raíz: si no hay sesión, va al login. Si hay, va a su área."""
    if 'id_area' in session:
        if session['id_area'] == 1:
            return redirect(url_for('prod_chrysopa.ocupacion'))
        elif session['id_area'] == 2:
            return redirect(url_for('prod_catopar.pre'))
        elif session['id_area'] == 3:
            return redirect(url_for('empaque.dashboard_empaque'))
        elif session['id_area'] == 4:
            return redirect(url_for('inventario.listar_solicitudes'))
        elif session['id_area'] == 5:
            return redirect(url_for('index'))
            
    return redirect(url_for('auth.login'))

@app.route('/menu')
def index():
    """Menú principal (solo para la Administración / id_area = 5)."""
    # Protegemos la ruta para que SOLO el área 5 (Admin) pueda verla
    if 'id_area' not in session or session['id_area'] != 5:
        # Si intenta entrar alguien que no es admin, lo saca al login
        return redirect(url_for('auth.login'))
        
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)