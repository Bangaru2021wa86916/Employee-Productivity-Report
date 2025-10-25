from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, get_jwt
)
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from passlib.hash import pbkdf2_sha256
import mysql.connector
from mysql.connector import pooling
import datetime
import logging
import os

# ----------------------------------------
# Logging
# ----------------------------------------
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ----------------------------------------
# Flask Setup
# ----------------------------------------
app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:8080"}})

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
limiter.init_app(app)

# ----------------------------------------
# Database Setup
# ----------------------------------------
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
except mysql.connector.Error as err:
    logger.error(f"❌ Failed to create connection pool: {err}")
    raise

def get_db_connection():
    return connection_pool.get_connection()

# ----------------------------------------
# JWT Setup
# ----------------------------------------
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=24)
jwt = JWTManager(app)
blacklisted_tokens = set()

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    return jwt_payload["jti"] in blacklisted_tokens

# ----------------------------------------
# Routes
# ----------------------------------------

@app.route('/')
def health():
    return jsonify({"status": "running"}), 200

# ---------- LOGIN ----------
@app.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user or not pbkdf2_sha256.verify(password, user["password_hash"]):
        return jsonify({"msg": "Invalid username or password"}), 401

    token = create_access_token(identity=username)
    return jsonify({"token": token}), 200


# ---------- GET ALL EMPLOYEES ----------
@app.route("/employees", methods=["GET"])
@jwt_required()
def get_employees():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productivity ORDER BY id ASC")
    employees = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"employees": employees}), 200


# ---------- UPDATE EMPLOYEE ----------
@app.route("/employee/<int:emp_id>", methods=["PUT"])
@jwt_required()
def update_employee(emp_id):
    data = request.get_json()
    name = data.get("name")
    role = data.get("role")
    feedback = data.get("feedback")
    rating = data.get("rating")

    if not all([name, role]):
        return jsonify({"msg": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE productivity
        SET name=%s, role=%s, feedback=%s, rating=%s, updated_at=CURRENT_TIMESTAMP
        WHERE id=%s
    """, (name, role, feedback, rating, emp_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"msg": "Employee updated successfully"}), 200


# ---------- ADD NEW EMPLOYEE ----------
@app.route("/add", methods=["POST"])
@jwt_required()
def add_employee():
    data = request.get_json()
    name = data.get("name")
    role = data.get("role")
    productivity = data.get("productivity", 0)
    feedback = data.get("feedback", "")
    rating = data.get("rating", None)

    # Validation
    if not name or not role:
        return jsonify({"msg": "Name and role are required"}), 400
    if not isinstance(productivity, int) or productivity < 0 or productivity > 100:
        return jsonify({"msg": "Productivity must be a valid percentage (0-100)"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO productivity (name, role, productivity, feedback, rating)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, role, productivity, feedback, rating))
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()

    return jsonify({"msg": "Employee added successfully", "id": new_id}), 201


# ---------- LOGOUT ----------
@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    blacklisted_tokens.add(jti)
    return jsonify({"msg": "Successfully logged out"}), 200


# ---------- MAIN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
