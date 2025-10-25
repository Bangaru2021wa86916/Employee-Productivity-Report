from flask import Flask, jsonify, request, make_response
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, get_jwt
)
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from passlib.hash import scrypt
import mysql.connector
from mysql.connector import pooling
import datetime
import logging
import os
from functools import wraps

# ----------------------------------------
# Logging Configuration
# ----------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ----------------------------------------
# Flask App Initialization
# ----------------------------------------
app = Flask(__name__)

# Enable CORS for frontend (port 8080)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:8080"}})

# ----------------------------------------
# Rate Limiter Setup
# ----------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
limiter.init_app(app)

# ----------------------------------------
# Database Configuration
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

# Create MySQL connection pool
try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)
    logger.info("✅ Database connection pool created successfully")
except mysql.connector.Error as err:
    logger.error(f"❌ Failed to create connection pool: {err}")
    raise


def get_db_connection():
    """Retrieve a connection from the pool."""
    try:
        return connection_pool.get_connection()
    except mysql.connector.Error as err:
        logger.error(f"Error getting connection from pool: {err}")
        raise


# ----------------------------------------
# DB Error Handling Decorator
# ----------------------------------------
def handle_db_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except mysql.connector.Error as err:
            logger.error(f"Database error in {func.__name__}: {err}")
            return jsonify({
                "status": "error",
                "msg": "Database error occurred",
                "error": str(err)
            }), 500
    return wrapper


# ----------------------------------------
# Health Check Route
# ----------------------------------------
@app.route('/')
@handle_db_error
def health_check():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.datetime.now().isoformat()
        }), 200
    finally:
        conn.close()


# ----------------------------------------
# JWT Configuration
# ----------------------------------------
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=24)
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_ERROR_MESSAGE_KEY"] = "msg"

jwt = JWTManager(app)
blacklisted_tokens = set()


@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in blacklisted_tokens


# ----------------------------------------
# Authentication Routes
# ----------------------------------------
@app.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    if not data:
        logger.error("No JSON data received in login request")
        return jsonify({"status": "error", "msg": "Missing JSON data"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        logger.error("Missing username or password in login request")
        return jsonify({"status": "error", "msg": "Username and password are required"}), 400

    if not username.isalnum():
        return jsonify({"status": "error", "msg": "Invalid username format"}), 400

    logger.info(f"Login attempt for user: {username}")
    conn = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, username, password_hash 
            FROM admins 
            WHERE username = %s
        """, (username,))
        admin = cursor.fetchone()

        if not admin:
            logger.warning(f"Login failed: User {username} not found")
            return jsonify({"status": "error", "msg": "Invalid username or password"}), 401

        if not scrypt.verify(password, admin["password_hash"]):
            logger.warning(f"Login failed: Invalid password for user {username}")
            return jsonify({"status": "error", "msg": "Invalid username or password"}), 401

        access_token = create_access_token(identity=username, additional_claims={"admin_id": admin["id"]})
        logger.info(f"✅ Login successful for user: {username}")

        response = jsonify({
            "status": "success",
            "msg": "Login successful",
            "token": access_token,
            "username": username
        })
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:8080'
        return response, 200

    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        return jsonify({"status": "error", "msg": "Unexpected error occurred"}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    blacklisted_tokens.add(jti)
    logger.info(f"✅ User logged out successfully. Token blacklisted: {jti}")
    return jsonify({"status": "success", "msg": "Successfully logged out"}), 200


# ----------------------------------------
# Get All Employees
# ----------------------------------------
@app.route("/employees", methods=["GET"])
@jwt_required()
def get_employees():
    try:
        current_user = get_jwt_identity()
        logger.info(f"User {current_user} requesting employee data")

        conn = get_db_connection()
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT id FROM admins WHERE username = %s", (current_user,))
            admin = cursor.fetchone()
            if not admin:
                return jsonify({"msg": "Unauthorized access"}), 403

            cursor.execute("""
                SELECT id, name, role, productivity, feedback, rating, 
                       created_at, updated_at 
                FROM productivity 
                ORDER BY name ASC
            """)
            employees = cursor.fetchall()

            for emp in employees:
                emp['created_at'] = emp['created_at'].isoformat() if emp['created_at'] else None
                emp['updated_at'] = emp['updated_at'].isoformat() if emp['updated_at'] else None

        logger.info(f"✅ Retrieved {len(employees)} employees")
        return jsonify({
            "status": "success",
            "count": len(employees),
            "employees": employees
        }), 200

    except mysql.connector.Error as db_err:
        logger.error(f"Database error while retrieving employees: {str(db_err)}")
        return jsonify({"status": "error", "msg": "Database error", "error": str(db_err)}), 500

    except Exception as e:
        logger.error(f"Unexpected error retrieving employees: {str(e)}")
        return jsonify({"status": "error", "msg": "Unexpected error", "error": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


# ----------------------------------------
# Update Employee
# ----------------------------------------
@app.route("/employee/<int:emp_id>", methods=["PUT"])
@jwt_required()
def update_employee(emp_id):
    try:
        current_user = get_jwt_identity()
        logger.info(f"User {current_user} updating employee {emp_id}")

        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "msg": "No update data provided"}), 400

        name = data.get("name")
        role = data.get("role")
        feedback = data.get("feedback")
        rating = data.get("rating")
        productivity = data.get("productivity")

        if not all([name, role]):
            return jsonify({"status": "error", "msg": "Name and role are required"}), 400

        if rating is not None and (not isinstance(rating, (int, float)) or rating < 0 or rating > 5):
            return jsonify({"status": "error", "msg": "Rating must be between 0 and 5"}), 400

        if productivity is not None and (not isinstance(productivity, int) or productivity < 0 or productivity > 100):
            return jsonify({"status": "error", "msg": "Productivity must be integer 0–100"}), 400

        conn = get_db_connection()
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT id FROM productivity WHERE id = %s", (emp_id,))
            if not cursor.fetchone():
                return jsonify({"status": "error", "msg": f"Employee ID {emp_id} not found"}), 404

            cursor.execute("""
                UPDATE productivity
                SET name=%s, role=%s, feedback=%s, rating=%s, 
                    productivity=COALESCE(%s, productivity),
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=%s
            """, (name, role, feedback, rating, productivity, emp_id))
            conn.commit()

            cursor.execute("SELECT * FROM productivity WHERE id = %s", (emp_id,))
            updated_employee = cursor.fetchone()

        logger.info(f"✅ Employee {emp_id} updated successfully")
        return jsonify({
            "status": "success",
            "msg": "Employee updated successfully",
            "employee": updated_employee
        }), 200

    except mysql.connector.Error as db_err:
        logger.error(f"Database error updating employee {emp_id}: {str(db_err)}")
        return jsonify({"status": "error", "msg": "Database error", "error": str(db_err)}), 500

    except Exception as e:
        logger.error(f"Unexpected error updating employee {emp_id}: {str(e)}")
        return jsonify({"status": "error", "msg": "Unexpected error", "error": str(e)}), 500

    finally:
        if conn and conn.is_connected():
            conn.close()


# ----------------------------------------
# Run App
# ----------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
