# user-service/app.py
from flask import Flask, request, jsonify
import mysql.connector
import os
import hashlib

app = Flask(__name__)

def get_db():
    return mysql.connector.connect(
        host     = os.getenv('DB_HOST',     'mysql'),
        user     = os.getenv('DB_USER',     'root'),
        password = os.getenv('DB_PASSWORD', 'rootpass'),
        database = os.getenv('DB_NAME',     'appdb')
    )

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/health')
def health():
    try:
        db = get_db()
        db.close()
        return jsonify({'service': 'user-service', 'status': 'up'})
    except Exception as e:
        return jsonify({'service': 'user-service', 'status': 'down', 'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id, name, email, created_at FROM users")
    users = cur.fetchall()
    cur.close()
    db.close()
    return jsonify(users)

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id, name, email, created_at FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    db.close()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user)

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not all(k in data for k in ['name', 'email', 'password']):
        return jsonify({'error': 'name, email, password required'}), 400

    db  = get_db()
    cur = db.cursor()
    try:
        cur.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (data['name'], data['email'], hash_password(data['password']))
        )
        db.commit()
        user_id = cur.lastrowid
    except mysql.connector.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 409
    finally:
        cur.close()
        db.close()

    return jsonify({'id': user_id, 'message': 'User created'}), 201

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    db   = get_db()
    cur  = db.cursor()
    cur.execute(
        "UPDATE users SET name = %s, email = %s WHERE id = %s",
        (data.get('name'), data.get('email'), user_id)
    )
    db.commit()
    cur.close()
    db.close()
    return jsonify({'message': 'User updated'})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    db  = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db.commit()
    cur.close()
    db.close()
    return jsonify({'message': 'User deleted'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)