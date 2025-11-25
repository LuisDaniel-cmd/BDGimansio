import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv

# Cargar las variables de entorno
load_dotenv()

app = Flask(__name__)
# Configurar la SECRET_KEY obligatoria para las sesiones
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# Función para conectarse a la BD de Neon
def get_db_connection():
    """
    Se conecta a la base de datos.
    Si el usuario está en una sesión, se conecta COMO ESE USUARIO.
    """
    try:
        # Intentar conectar usando las credenciales de la sesión
        conn = psycopg2.connect(
            host=os.environ.get('NEON_HOST'),
            dbname=os.environ.get('NEON_DBNAME'),
            user=session.get('username'), # Toma el usuario de la sesión
            password=session.get('password') # Toma la contraseña de la sesión
        )
        return conn
    except psycopg2.Error as e:
        print(f"Error al conectar como {session.get('username')}: {e}")
        return None
    except Exception as e:
        # Captura el error si 'username' o 'password' no están en la sesión
        print(f"Error de sesión: {e}")
        return None

# --- RUTAS DE AUTENTICACIÓN ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si el usuario ya está logueado, lo mandamos al dashboard
    if 'username' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Intento de conexión "de prueba"
        try:
            conn_test = psycopg2.connect(
                host=os.environ.get('NEON_HOST'),
                dbname=os.environ.get('NEON_DBNAME'),
                user=username,
                password=password
            )
            conn_test.close()
            
            session['username'] = username
            session['password'] = password
            
            # Buscamos el rol de este usuario
            conn = get_db_connection()
            with conn.cursor() as cur:
                 # Esta consulta es más robusta
                 cur.execute("""
                     SELECT r.rolname 
                     FROM pg_roles r
                     JOIN pg_auth_members m ON m.roleid = r.oid
                     JOIN pg_user u ON m.member = u.usesysid
                     WHERE u.usename = %s;
                 """, (username,))
                 user_role = cur.fetchone()
                 if user_role:
                     session['role'] = user_role[0]
                 else:
                     session['role'] = username # Si no tiene rol, es el propio usuario
            conn.close()

            flash(f'¡Bienvenido {username} (Rol: {session["role"]})!', 'success')
            return redirect(url_for('dashboard'))

        except psycopg2.Error as e:
            flash('Usuario o contraseña incorrectos.', 'danger')
            print(f"Fallo de login para {username}: {e}")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear() # Borra toda la sesión
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('login'))

# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', rol=session.get('role'))

@app.route('/miembros')
def miembros_index():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        flash('Error de conexión. ¿Estás logueado?', 'danger')
        return redirect(url_for('login'))
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id_miembro, full_name, correo, tipo_membresia FROM miembro ORDER BY id_miembro;")
            miembros = cur.fetchall()
        conn.close()
        return render_template('index.html', miembros=miembros, rol=session.get('role'))
        
    except psycopg2.Error as e:
        conn.close()
        flash(f'Error de permisos: No puedes ver esta tabla ({e.pgcode}: {e.pgerror}).', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/clases')
def clases_index():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    if conn is None:
        flash('Error de conexión. ¿Estás logueado?', 'danger')
        return redirect(url_for('login'))

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.nombre AS clase, c.horario, i.nombre AS instructor
                FROM clase c
                JOIN instructor i ON c.instructor_id = i.id_instructor
                ORDER BY c.horario;
            """)
            clases = cur.fetchall()
        conn.close()
        
        return render_template('clases.html', clases=clases, rol=session.get('role'))

    except psycopg2.Error as e:
        conn.close()
        flash(f'Error de permisos: No puedes ver esta tabla ({e.pgcode}: {e.pgerror}).', 'danger')
        return redirect(url_for('dashboard'))

# --- RUTA PARA AGREGAR MIEMBROS ---

@app.route('/miembro/nuevo', methods=['GET', 'POST'])
def miembro_nuevo():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    # --- LÓGICA DEL POST (Cuando se envía el formulario) ---
    if request.method == 'POST':
        conn = get_db_connection()
        if conn is None:
            flash('Error de conexión.', 'danger')
            return redirect(url_for('login'))
            
        try:
            # 1. Obtener datos del formulario
            nombre = request.form['nombre']
            apellido_paterno = request.form['apellido_paterno']
            correo = request.form['correo']
            tipo_membresia = request.form['tipo_membresia']

            # 2. Ejecutar el INSERT
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO miembro (nombre, apellido_paterno, correo, tipo_membresia)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (nombre, apellido_paterno, correo, tipo_membresia)
                )
                conn.commit() # ¡Importante! Guardar los cambios
            conn.close()
            
            flash('¡Miembro agregado exitosamente!', 'success')
            return redirect(url_for('miembros_index')) # Redirige a la lista de miembros

        except psycopg2.Error as e:
            conn.rollback() # Deshace el INSERT si falló
            conn.close()
            if e.pgcode == '23505': # Unique violation
                 flash(f'Error: El correo "{correo}" ya está registrado.', 'danger')
            elif e.pgcode == '42501': # Permission denied
                flash(f'Error de permisos: ¡No tienes permiso para agregar miembros!', 'danger')
            else:
                flash(f'Error inesperado al agregar miembro: {e.pgerror}', 'danger')
            
            return redirect(url_for('miembro_nuevo')) # Regresa al formulario

    # --- LÓGICA DEL GET (Solo mostrar la página) ---
    return render_template('miembro_nuevo.html', rol=session.get('role'))


# --- (NUEVO) RUTA PARA VER PAGOS ---

@app.route('/pagos')
def pagos_index():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    if conn is None:
        flash('Error de conexión. ¿Estás logueado?', 'danger')
        return redirect(url_for('login'))

    try:
        with conn.cursor() as cur:
            # Esta consulta une pago y miembro para mostrar el nombre
            cur.execute("""
                SELECT m.full_name, p.monto, p.fecha_pago, p.metodo_pago
                FROM pago p
                JOIN miembro m ON p.miembro_id = m.id_miembro
                ORDER BY p.fecha_pago DESC;
            """)
            pagos = cur.fetchall()
        conn.close()
        
        # Renderiza la NUEVA plantilla 'pagos.html'
        return render_template('pagos.html', pagos=pagos, rol=session.get('role'))

    except psycopg2.Error as e:
        conn.close()
        # Esta es la demostración: Si 'instructor' entra, fallará.
        flash(f'Error de permisos: No puedes ver esta tabla ({e.pgcode}: {e.pgerror}).', 'danger')
        return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)