import sqlite3
from flask import Flask, render_template, request, redirect, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_sesiones'
DB_NAME = 'gastos.db'

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class Usuario(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

def obtener_conexion():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@login_manager.user_loader
def load_user(user_id):
    conn = obtener_conexion()
    u = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if u:
        return Usuario(u['id'], u['username'])
    return None

def inicializar_db():
    conn = obtener_conexion()
    # Tabla de usuarios
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Tabla de transacciones vinculada a cada usuario
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            categoria TEXT NOT NULL,
            monto REAL NOT NULL,
            descripcion TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    conn.commit()
    conn.close()

# --- RUTAS DE AUTENTICACIÓN ---

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        conn = obtener_conexion()
        try:
            conn.execute('INSERT INTO usuarios (username, password) VALUES (?, ?)', (username, password_hash))
            conn.commit()
            conn.close()
            return redirect('/login')
        except sqlite3.IntegrityError:
            conn.close()
            flash('El nombre de usuario ya existe.')
            return redirect('/registro')

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = obtener_conexion()
        user = conn.execute('SELECT * FROM usuarios WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            usuario_obj = Usuario(user['id'], user['username'])
            login_user(usuario_obj)
            return redirect('/')
        else:
            flash('Usuario o contraseña incorrectos.')
            return redirect('/login')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

# --- RUTAS DE TRANSACCIONES ---

# Filtro para formatear montos con punto de miles (ej: 3.100.000)
@app.template_filter('formato_moneda')
def formato_moneda(valor):
    try:
        if valor is None:
            return "0"
        return f"{int(valor):,}".replace(",", ".")
    except (ValueError, TypeError):
        return valor

@app.route('/', methods=['GET', 'POST'])
@login_required
def inicio():
    conn = obtener_conexion()
    
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        categoria = request.form.get('categoria')
        monto = request.form.get('monto')
        descripcion = request.form.get('descripcion', '').strip()
        
        # Validación backend de campos obligatorios (incluyendo descripción)
        if not tipo or not categoria or not monto or not descripcion:
            flash('Todos los campos son obligatorios, incluyendo la descripción.')
            conn.close()
            return redirect('/')

        try:
            monto_float = float(monto)
        except ValueError:
            flash('El monto debe ser un número válido.')
            conn.close()
            return redirect('/')

        conn.execute(
            'INSERT INTO transacciones (usuario_id, tipo, categoria, monto, descripcion) VALUES (?, ?, ?, ?, ?)',
            (current_user.id, tipo, categoria, monto_float, descripcion)
        )
        conn.commit()
        conn.close()
        return redirect('/')

    categoria_filtro = request.args.get('categoria', '')
    
    # Obtener únicamente las categorías únicas cargadas por este usuario para el filtro dinámico
    categorias_unicas = conn.execute(
        'SELECT DISTINCT categoria FROM transacciones WHERE usuario_id = ? ORDER BY categoria ASC', 
        (current_user.id,)
    ).fetchall()

    if categoria_filtro:
        transacciones = conn.execute(
            'SELECT * FROM transacciones WHERE usuario_id = ? AND categoria = ? ORDER BY id DESC', 
            (current_user.id, categoria_filtro)
        ).fetchall()
    else:
        transacciones = conn.execute(
            'SELECT * FROM transacciones WHERE usuario_id = ? ORDER BY id DESC', 
            (current_user.id,)
        ).fetchall()

    ingresos = conn.execute(
        "SELECT SUM(monto) FROM transacciones WHERE usuario_id = ? AND tipo='Ingreso'", 
        (current_user.id,)
    ).fetchone()[0] or 0

    gastos = conn.execute(
        "SELECT SUM(monto) FROM transacciones WHERE usuario_id = ? AND tipo='Gasto'", 
        (current_user.id,)
    ).fetchone()[0] or 0

    saldo = ingresos - gastos
    conn.close()

    return render_template(
        'index.html',
        transacciones=transacciones,
        ingresos=ingresos,
        gastos=gastos,
        saldo=saldo,
        categorias=categorias_unicas,
        categoria_filtro=categoria_filtro
    )

@app.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    conn = obtener_conexion()
    conn.execute('DELETE FROM transacciones WHERE id = ? AND usuario_id = ?', (id, current_user.id))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    conn = obtener_conexion()
    
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        categoria = request.form.get('categoria')
        monto = request.form.get('monto')
        descripcion = request.form.get('descripcion', '').strip()
        
        if not tipo or not categoria or not monto or not descripcion:
            flash('Todos los campos son obligatorios.')
            conn.close()
            return redirect(f'/editar/{id}')

        conn.execute('''
            UPDATE transacciones 
            SET tipo = ?, categoria = ?, monto = ?, descripcion = ?
            WHERE id = ? AND usuario_id = ?
        ''', (tipo, categoria, monto, descripcion, id, current_user.id))
        conn.commit()
        conn.close()
        return redirect('/')

    transaccion = conn.execute(
        'SELECT * FROM transacciones WHERE id = ? AND usuario_id = ?', 
        (id, current_user.id)
    ).fetchone()
    conn.close()
    
    if not transaccion:
        return redirect('/')

    return render_template('editar.html', transaccion=transaccion)

# --- API ENDPOINTS ---
@app.route('/api/resumen', methods=['GET'])
@login_required
def api_resumen():
    conn = obtener_conexion()
    ingresos = conn.execute(
        "SELECT SUM(monto) FROM transacciones WHERE usuario_id = ? AND tipo='Ingreso'", 
        (current_user.id,)
    ).fetchone()[0] or 0

    gastos = conn.execute(
        "SELECT SUM(monto) FROM transacciones WHERE usuario_id = ? AND tipo='Gasto'", 
        (current_user.id,)
    ).fetchone()[0] or 0

    saldo = ingresos - gastos
    conn.close()

    return jsonify({
        'ingresos': ingresos,
        'gastos': gastos,
        'saldo': saldo
    })

@app.route('/api/transacciones', methods=['GET'])
@login_required
def api_listar_transacciones():
    conn = obtener_conexion()
    filas = conn.execute(
        'SELECT id, tipo, categoria, monto, descripcion FROM transacciones WHERE usuario_id = ? ORDER BY id DESC',
        (current_user.id,)
    ).fetchall()
    conn.close()

    lista_transacciones = [dict(row) for row in filas]
    return jsonify(lista_transacciones), 200

@app.route('/api/transacciones', methods=['POST'])
@login_required
def api_crear_transaccion():
    datos = request.get_json(silent=True) or request.form

    tipo = datos.get('tipo')
    categoria = datos.get('categoria')
    monto = datos.get('monto')
    descripcion = datos.get('descripcion', '').strip()

    # Requisito HTTP 400 Bad Request si falta algún campo obligatorio (incluyendo descripción)
    if not tipo or not categoria or not monto or not descripcion:
        return jsonify({
            'error': 'Datos incompletos',
            'mensaje': 'Los campos Movimiento, Categoría, Monto y Descripción son obligatorios.'
        }), 400

    try:
        monto_float = float(monto)
    except ValueError:
        return jsonify({
            'error': 'Formato inválido',
            'mensaje': 'El campo monto debe ser un número válido.'
        }), 400

    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO transacciones (usuario_id, tipo, categoria, monto, descripcion) VALUES (?, ?, ?, ?, ?)',
        (current_user.id, tipo, categoria, monto_float, descripcion)
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()

    return jsonify({
        'mensaje': 'Transacción creada exitosamente',
        'transaccion': {
            'id': nuevo_id,
            'tipo': tipo,
            'categoria': categoria,
            'monto': monto_float,
            'descripcion': descripcion
        }
    }), 201

# --- ARRANQUE DE LA APLICACIÓN ---
inicializar_db()

if __name__ == '__main__':
    app.run(debug=True)