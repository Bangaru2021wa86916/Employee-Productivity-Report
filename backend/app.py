# backend/app.py
from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, get_jwt
)
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from passlib.hash import pbkdf2_sha256
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector
from mysql.connector import pooling
import datetime
import logging
import os

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

db_config = {
    'host': os.getenv('MYSQL_HOST', 'db'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'password'),
    'database': os.getenv('MYSQL_DATABASE', 'employee_db'),
    'auth_plugin': 'mysql_native_password',
    'pool_name': 'mypool',
    'pool_size': 5
}

try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)
    logger.info("✅ Database connection pool created successfully")
except Exception as err:
    logger.exception("❌ Failed to create connection pool: %s", err)
    raise

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=24)
jwt = JWTManager(app)
blacklisted_tokens = set()

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    return jwt_payload["jti"] in blacklisted_tokens

def get_db_connection():
    return connection_pool.get_connection()

def verify_password(plain_password, stored_hash):
    if stored_hash is None:
        return False
    try:
        if stored_hash.startswith("$pbkdf2-sha256$"):
            return pbkdf2_sha256.verify(plain_password, stored_hash)
    except Exception:
        logger.debug("passlib verify failed")
    try:
        if check_password_hash(stored_hash, plain_password):
            return True
    except Exception:
        logger.debug("werkzeug check failed")
    try:
        if plain_password == stored_hash:
            logger.warning("Password stored in plaintext!")
            return True
    except Exception:
        pass
    return False

@app.route('/')
def health():
    return jsonify({"status": "running"}), 200

@app.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
        user = cursor.fetchone()
    except Exception as e:
        logger.exception("Database error during login: %s", e)
        return jsonify({"msg": "Database error"}), 500
    finally:
        try:
            cursor.close(); conn.close()
        except Exception:
            pass
    if not user:
        return jsonify({"msg": "Invalid username or password"}), 401
    stored_hash = user.get("password_hash")
    if not verify_password(password, stored_hash):
        return jsonify({"msg": "Invalid username or password"}), 401
    access_token = create_access_token(identity=user['username'])
    return jsonify({"access_token": access_token}), 200

@app.route('/setup-admin', methods=['POST'])
def setup_admin():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'msg': 'username and password required'}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM admins")
        count = cursor.fetchone()[0]
        if count > 0:
            return jsonify({'msg': 'Admin already exists'}), 400
        hashed = pbkdf2_sha256.hash(password)
        cursor.execute("INSERT INTO admins (username, password_hash) VALUES (%s, %s)", (username, hashed))
        conn.commit()
    except Exception as e:
        logger.exception("Error creating admin: %s", e)
        return jsonify({'msg': 'Error creating admin'}), 500
    finally:
        try:
            cursor.close(); conn.close()
        except Exception:
            pass
    return jsonify({'msg': 'Admin created'}), 201

@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    blacklisted_tokens.add(jti)
    return jsonify({"msg": "Successfully logged out"}), 200

@app.route('/employees', methods=['GET'])
@jwt_required()
def get_employees():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM productivity ORDER BY id ASC")
        employees = cursor.fetchall()
    except Exception as e:
        logger.exception("Error fetching employees: %s", e)
        return jsonify({'msg': 'Error fetching employees'}), 500
    finally:
        try:
            cursor.close(); conn.close()
        except Exception:
            pass
    return jsonify({'employees': employees}), 200

# Add a new employee (used by frontend /add)
@app.route("/add", methods=["POST"])
@jwt_required()
def add_employee():
    data = request.get_json() or {}
    name = data.get("name")
    role = data.get("role")
    productivity = data.get("productivity", 0)
    feedback = data.get("feedback", "")
    rating = data.get("rating", None)
    if not name or not role:
        return jsonify({'msg': 'name and role required'}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO productivity (name, role, productivity, feedback, rating) VALUES (%s,%s,%s,%s,%s)",
            (name, role, productivity, feedback, rating)
        )
        conn.commit()
    except Exception as e:
        logger.exception("Error adding employee: %s", e)
        return jsonify({'msg': 'Error adding employee'}), 500
    finally:
        try:
            cursor.close(); conn.close()
        except Exception:
            pass
    return jsonify({'msg': 'Employee added'}), 201

# Update employee
@app.route("/employee/<int:emp_id>", methods=["PUT"])
@jwt_required()
def update_employee(emp_id):
    data = request.get_json() or {}
    name = data.get("name")
    role = data.get("role")
    feedback = data.get("feedback")
    rating = data.get("rating")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE productivity SET name=%s, role=%s, feedback=%s, rating=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
            (name, role, feedback, rating, emp_id)
        )
        conn.commit()
    except Exception as e:
        logger.exception("Error updating employee: %s", e)
        return jsonify({'msg': 'Error updating employee'}), 500
    finally:
        try:
            cursor.close(); conn.close()
        except Exception:
            pass
    return jsonify({'msg': 'Employee updated'}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
