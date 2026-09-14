from flask import Blueprint, render_template

# Tu blueprint de producción (asegúrate de que el nombre coincida con el tuyo)
prod_chrysopa_bp = Blueprint('prod_chrysopa', __name__, url_prefix='/piso/chrysopa')

@prod_chrysopa_bp.route('/ocupacion')
def ocupacion():
    return render_template('produccion/chrysopa/ocupacion.html')

@prod_chrysopa_bp.route('/pupacion')
def pupacion():
    # Cambia esto por tu render_template cuando tengas el archivo listo
    return render_template('produccion/chrysopa/pupacion.html')

@prod_chrysopa_bp.route('/eclosion')
def eclosion():
    return render_template('produccion/chrysopa/eclosion.html')

@prod_chrysopa_bp.route('/mortalidad')
def mortalidad():
    return render_template('produccion/chrysopa/mortalidad.html')

@prod_chrysopa_bp.route('/fallas')
def fallas():
    return render_template('produccion/chrysopa/fallas.html')

@prod_chrysopa_bp.route('/materiales')
def materiales():
    # Renderizamos el MISMO archivo, pero le decimos que el origen es 'chrysopa'
    return render_template('produccion/materiales.html', origen='chrysopa')