import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

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


# Asegúrate de tener tu función de conexión
def get_db_connection():
    conn = sqlite3.connect('Bd_SIO-AGRO.db', isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn

# 1. RUTA PARA VER LA PANTALLA Y EL HISTORIAL
@prod_chrysopa_bp.route('/materiales', methods=['GET'])
def materiales():
    id_operador = session.get('id_usuario')
    
    # Si no hay sesión, regresamos al login
    if not id_operador:
        flash('Sesión expirada. Vuelve a iniciar sesión.', 'error')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Consultamos las solicitudes hechas por este operador
    cursor.execute("""
        SELECT s.id_solicitud, s.fecha_solicitud, s.cantidad_solicitada, s.estatus,
               m.nombre_material, u.nombre_usuario
        FROM SOLICITUDES_MATERIAL s
        JOIN MATERIALES m ON s.id_material = m.id_material
        JOIN USUARIOS u ON s.id_operador = u.id_usuario
        WHERE s.id_operador = ?
        ORDER BY s.fecha_solicitud DESC
    """, (id_operador,))
    
    # ¡ESTA ES LA LÍNEA QUE FALTABA PARA QUE FUNCIONE!
    mis_solicitudes = cursor.fetchall() 
    conn.close()
    
    # Pasamos los datos al HTML
    return render_template('produccion/materiales.html', origen='chrysopa', mis_solicitudes=mis_solicitudes)


# 2. RUTA PARA GUARDAR EL FORMULARIO
@prod_chrysopa_bp.route('/materiales/guardar', methods=['POST'])
def guardar_materiales():
    nip_ingresado = request.form.get('nip')
    id_operador = session.get('id_usuario')
    id_area = session.get('id_area')

    print("\n--- INTENTO DE PEDIDO DE MATERIALES ---")
    print(f"Operador ID: {id_operador} | Área: {id_area} | NIP ingresado: '{nip_ingresado}'")

    if not id_operador:
        flash('Sesión expirada. Vuelve a iniciar sesión.', 'error')
        return redirect(url_for('auth.login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Validar el NIP
        cursor.execute("SELECT nip_firma FROM USUARIOS WHERE id_usuario = ?", (id_operador,))
        usuario = cursor.fetchone()
        
        nip_real = str(usuario['nip_firma']) if usuario else 'Ninguno'
        print(f"NIP real en BD: '{nip_real}'")
        
        if not usuario or nip_real != str(nip_ingresado):
            print("❌ ERROR: El NIP no coincide.")
            flash('Firma (NIP) incorrecta. Tu pedido no fue enviado.', 'error')
            return redirect(url_for('prod_chrysopa.materiales'))

        print("✅ NIP correcto. Revisando materiales...")
        materiales_guardados = 0

        # Guardar cada material marcado en el formulario (1 al 4)
        for i in range(1, 5):
            checkbox = request.form.get(f'material_{i}')
            if checkbox: # Si el checkbox fue marcado en HTML
                cantidad = request.form.get(f'cant_{i}')
                cantidad_final = int(cantidad) if cantidad and cantidad.isdigit() else 1
                
                print(f"  -> Insertando Material ID: {i} | Cantidad: {cantidad_final}")

                cursor.execute("""
                    INSERT INTO SOLICITUDES_MATERIAL (id_area_solicitante, id_operador, id_material, cantidad_solicitada, estatus)
                    VALUES (?, ?, ?, ?, 'Pendiente')
                """, (id_area, id_operador, i, cantidad_final))
                
                materiales_guardados += 1

        # ESTA LÍNEA ES LA QUE OBLIGA A GUARDAR EN LA BD
        if materiales_guardados > 0:
            conn.commit() 
            print(f"✅ ÉXITO: {materiales_guardados} materiales insertados en la base de datos.")
            flash(f'¡Listo! Se solicitaron {materiales_guardados} materiales al almacén.', 'success')
        else:
            print("⚠️ ADVERTENCIA: No se marcó ninguna casilla.")
            flash('No seleccionaste ningún material para pedir.', 'error')

    except Exception as e:
        print(f"❌ ERROR SQL FATAL: {e}")
        flash(f'Error interno del sistema: {str(e)}', 'error')
    finally:
        conn.close()
        print("--- FIN DEL INTENTO ---\n")

    return redirect(url_for('prod_chrysopa.materiales'))