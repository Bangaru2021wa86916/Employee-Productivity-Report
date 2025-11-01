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

# ------------------ App setup ------------------
app = Flask(__name__)
CORS(app)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

# Database configuration (reads from env with sensible defaults)
db_config = {
    'host': os.getenv('MYSQL_HOST', 'db'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'password'),
    'database': os.getenv('MYSQL_DATABASE', 'employee_db'),
    'auth_plugin': 'mysql_native_password',
    'pool_name': 'mypool',
    'pool_size': 5
}

# Try to create connection pool
try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)
    logger.info("✅ Database connection pool created successfully")
except Exception as err:
    logger.exception("❌ Failed to create connection pool: %s", err)
    # Re-raise so container will show error in logs
    raise

# JWT Setup
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=24)
jwt = JWTManager(app)
blacklisted_tokens = set()

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    return jwt_payload["jti"] in blacklisted_tokens

# Helper: get DB connection
def get_db_connection():
    return connection_pool.get_connection()

# Helper: robust password verification
def verify_password(plain_password, stored_hash):
    """Try several common hash formats and return True if matches.
    Supports passlib pbkdf2_sha256 ($pbkdf2-sha256$...), werkzeug hashes (scrypt, pbkdf2:sha256...), and a direct pbkdf2_sha256 verify.
    """
    if stored_hash is None:
        return False
    # Try passlib pbkdf2_sha256 first
    try:
        if stored_hash.startswith("$pbkdf2-sha256$"):
            return pbkdf2_sha256.verify(plain_password, stored_hash)
    except Exception:
        # continue to other checks
        logger.debug("passlib verify failed for hash: %s", stored_hash[:40])

    # Try werkzeug's check_password_hash (handles several schemes including scrypt/pbkdf2)
    try:
        if check_password_hash(stored_hash, plain_password):
            return True
    except Exception:
        logger.debug("werkzeug check_password_hash failed to parse hash: %s", stored_hash[:40])

    # As a last-resort: try direct equality with plain (only for debugging; not recommended for prod)
    try:
        if plain_password == stored_hash:
            logger.warning("Password stored in plaintext! Consider migrating to a hashed password.")
            return True
    except Exception:
        pass

    return False

# Health
@app.route('/')
def health():
    return jsonify({"status": "running"}), 200

# ---------- LOGIN ----------
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
            cursor.close()
            conn.close()
        except Exception:
            pass

    if not user:
        return jsonify({"msg": "Invalid username or password"}), 401

    stored_hash = user.get("password_hash")
    if not verify_password(password, stored_hash):
        return jsonify({"msg": "Invalid username or password"}), 401

    access_token = create_access_token(identity=user['username'])
    return jsonify({"access_token": access_token}), 200

# Optional: setup-admin route useful when DB is empty. Only create admin if none exists.
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
        # Hash password using werkzeug or passlib
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

# ---------- LOGOUT ----------
@app.route("/logout", methods=["POST"]) 
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    blacklisted_tokens.add(jti)
    return jsonify({"msg": "Successfully logged out"}), 200

# ---------- Example protected route ----------
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

# ---------- MAIN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
