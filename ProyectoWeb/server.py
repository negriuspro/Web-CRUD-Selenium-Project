import os
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import pyodbc
from werkzeug.security import generate_password_hash, check_password_hash


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEBAPP_DIR = os.path.join(BASE_DIR, "webapp")

app = Flask(__name__, static_folder=WEBAPP_DIR, static_url_path='')
app.secret_key = 'tu_clave_secreta_aqui' 
CORS(app, supports_credentials=True)


driver = '{ODBC Driver 18 for SQL Server}'
server = 'ANGEL\\SQLEXPRESS01'
database = 'ProyectoWebDB'

conn_str = (
    f"DRIVER={driver};"
    f"SERVER={server};"
    f"DATABASE={database};"
    "Trusted_Connection=yes;"
    "Encrypt=no;"
)

def get_cursor():
    conn = pyodbc.connect(conn_str)
    return conn, conn.cursor()


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email y password son obligatorios'}), 400

    conn, cursor = get_cursor()
    try:
        cursor.execute("SELECT id, password FROM Users WHERE email = ?", (email,))
        row = cursor.fetchone()

        if not row:
            return jsonify({'message': 'Credenciales incorrectas'}), 401

        stored = row[1]

        if stored == password or check_password_hash(stored, password):
      
            session['user_id'] = row[0]
            session['logged'] = True
            return jsonify({'message': 'Login exitoso', 'user_id': row[0]}), 200
        else:
            return jsonify({'message': 'Credenciales incorrectas'}), 401

    except Exception as e:
        return jsonify({'message': 'Error en servidor', 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/check_session', methods=['GET'])
def check_session():
    if session.get('logged'):
        return jsonify({'logged': True, 'user_id': session.get('user_id')}), 200
    return jsonify({'logged': False}), 401


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logout exitoso'}), 200


@app.route('/api/users', methods=['GET'])
def get_all_users():
    if not session.get('logged'):
        return jsonify({'message': 'No autorizado'}), 401

    conn, cursor = get_cursor()
    try:
        cursor.execute("SELECT id, username, email FROM Users")
        users = [{'id': r[0], 'username': r[1], 'email': r[2]} for r in cursor.fetchall()]
        return jsonify(users), 200
    except Exception as e:
        return jsonify({'message': 'Error al obtener usuarios', 'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    if not session.get('logged'):
        return jsonify({'message': 'No autorizado'}), 401

    conn, cursor = get_cursor()
    try:
        cursor.execute("SELECT id, username, email, password FROM Users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return jsonify({'id': row[0], 'username': row[1], 'email': row[2], 'password': row[3]}), 200
        return jsonify({'message': 'Usuario no encontrado'}), 404
    except Exception as e:
        return jsonify({'message': 'Error al obtener usuario', 'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/users', methods=['POST'])
def create_user():
    if not session.get('logged'):
        return jsonify({'message': 'No autorizado'}), 401

    data = request.get_json() or {}
    email = (data.get('email') or '').strip()
    password = data.get('password')
    username = (data.get('username') or '').strip() or email

    if not email or not password:
        return jsonify({'message': 'Email y password son obligatorios'}), 400

    conn, cursor = get_cursor()
    try:
        cursor.execute("SELECT id FROM Users WHERE email = ?", (email,))
        if cursor.fetchone():
            return jsonify({'message': 'Email ya existe'}), 400

        stored_pass = password 
        cursor.execute("INSERT INTO Users (username, email, password) VALUES (?, ?, ?)", (username, email, stored_pass))
        conn.commit()
        return jsonify({'message': 'Usuario creado'}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'message': 'Error al crear usuario', 'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    if not session.get('logged'):
        return jsonify({'message': 'No autorizado'}), 401

    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password')

    if not username or not email:
        return jsonify({'message': 'Username y email son obligatorios'}), 400

    conn, cursor = get_cursor()
    try:
        cursor.execute("SELECT id FROM Users WHERE email = ? AND id <> ?", (email, user_id))
        if cursor.fetchone():
            return jsonify({'message': 'Email ya existe para otro usuario'}), 400

        if password:
            stored_pass = password
            cursor.execute("UPDATE Users SET username=?, email=?, password=? WHERE id=?", (username, email, stored_pass, user_id))
        else:
            cursor.execute("UPDATE Users SET username=?, email=? WHERE id=?", (username, email, user_id))
        conn.commit()
        return jsonify({'message': 'Usuario actualizado'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'message': 'Error al actualizar usuario', 'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if not session.get('logged'):
        return jsonify({'message': 'No autorizado'}), 401

    conn, cursor = get_cursor()
    try:
        cursor.execute("DELETE FROM Users WHERE id = ?", (user_id,))
        conn.commit()
        return jsonify({'message': 'Usuario eliminado'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'message': 'Error al eliminar usuario', 'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_frontend(path):
    full_path = os.path.join(WEBAPP_DIR, path)
    if os.path.exists(full_path):
        return send_from_directory(WEBAPP_DIR, path)
    return f"Archivo no encontrado: {path}", 404


if __name__ == '__main__':
    if os.path.isdir(WEBAPP_DIR):
        print("Archivos en webapp:", os.listdir(WEBAPP_DIR))
    else:
        print("Directorio webapp no encontrado:", WEBAPP_DIR)

    app.run(debug=True, host='0.0.0.0', port=5000)
