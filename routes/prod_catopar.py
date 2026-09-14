from flask import Blueprint, render_template

prod_catopar_bp = Blueprint('prod_catopar', __name__, url_prefix='/piso/catopar')

# 1. Ruta que ya tenías (Pre-Parasitismo)
@prod_catopar_bp.route('/pre', methods=['GET'])
def pre():
    return render_template('produccion/catopar/pre.html')

# 2. NUEVA RUTA: Post-Parasitismo
@prod_catopar_bp.route('/post', methods=['GET'])
def post():
    # Asegúrate de que este archivo HTML exista en tus carpetas
    return render_template('produccion/catopar/post.html')

@prod_catopar_bp.route('/materiales')
def materiales():
    # Renderizamos el mismo archivo, pero le decimos que el origen es 'catopar'
    return render_template('produccion/materiales.html', origen='catopar')