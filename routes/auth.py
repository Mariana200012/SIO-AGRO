from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import get_db_connection

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya hay sesión, lo enviamos a su área según su ID numérico
    if 'id_area' in session:
        return redirigir_por_area(session['id_area'])

    if request.method == 'POST':
        nip_ingresado = request.form.get('nip')
        
        # Chivato: Qué NIP está llegando de la página web
        print(f"\n--- DEBUG DE LOGIN ---")
        print(f"NIP escrito en la pantalla: '{nip_ingresado}'")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscamos usando el nombre exacto de tu columna: 'nip_firma'
        cursor.execute('''
            SELECT id_usuario, nombre_usuario, id_area, puesto 
            FROM USUARIOS 
            WHERE nip_firma = ?
        ''', (nip_ingresado,))
        
        usuario = cursor.fetchone()
        conn.close()
        
        if usuario:
            # Chivato: Qué datos encontró en tu BD real
            print(f"¡Éxito! Usuario: {usuario['nombre_usuario']} | id_area: {usuario['id_area']}\n")
            
            # Guardamos los datos de tu tabla en la sesión actual
            session['id_usuario'] = usuario['id_usuario']
            session['nombre'] = usuario['nombre_usuario']
            session['id_area'] = usuario['id_area']
            session['puesto'] = usuario['puesto']
            
            return redirigir_por_area(usuario['id_area'])
        else:
            # Chivato: Fallo total
            print("FALLO: La base de datos dice que ese NIP no existe en la columna nip_firma.\n")
            flash('NIP incorrecto o no registrado.', 'error')
            return redirect(url_for('auth.login'))
            
    # ¡ESTA ES LA LÍNEA QUE FALTABA! Maneja las peticiones GET (cargar la página web sin errores)
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


def redirigir_por_area(id_area):
    """Redirige al usuario evaluando el id_area de tu tabla 'areas'."""
    if id_area == 1:
        # 1 = Chrysopa
        return redirect(url_for('prod_chrysopa.ocupacion'))
    elif id_area == 2:
        # 2 = Catopar
        return redirect(url_for('prod_catopar.pre'))
    elif id_area == 3:
        # 3 = Empaque
        return redirect(url_for('empaque.dashboard_empaque')) 
    elif id_area == 4:
        # 4 = Inventario
        return redirect(url_for('inventario.listar_solicitudes')) 
    elif id_area == 5:
        # 5 = Administracion
        return redirect(url_for('index'))
    else:
        # Si el área no existe o está en blanco, se cierra la sesión
        session.clear()
        return redirect(url_for('auth.login'))