from flask import Flask, jsonify, request, make_response        
from flask_jwt_extended import (JWTManager, create_access_token, jwt_required,get_jwt_identity, get_jwt)
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from passlib.hash import scrypt
import mysql.connector
from mysql.connector import pooling
import datetime
import logging
import time
import os
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
limiter.init_app(app)
# Database configuration
db_config = {
    'host': os.getenv('MYSQL_HOST', 'db'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'password'),
    'database': os.getenv('MYSQL_DATABASE', 'employee_db'),
    'auth_plugin': 'mysql_native_password',
    'pool_name': 'mypool',
    'pool_size': 5
}

# Create connection pool
try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)
    logger.info("Database connection pool created successfully")
except mysql.connector.Error as err:
    logger.error(f"Failed to create connection pool: {err}")
    raise

def get_db_connection():
    try:
        return connection_pool.get_connection()
    except mysql.connector.Error as err:
        logger.error(f"Error getting connection from pool: {err}")
        raise

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

# JWT setup with longer expiration
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-key")  # Load from environment
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=24)  # Extended for testing
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_ERROR_MESSAGE_KEY"] = "msg"  # Consistent error message key
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config["JWT_BLACKLIST_TOKEN_CHECKS"] = ["access"]

jwt = JWTManager(app)
blacklisted_tokens = set()

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in blacklisted_tokens

# --- Authentication endpoints ---
@app.route("/login", methods=["POST"])
@limiter.limit("5 per minute")  # Rate limiting for login attempts
@handle_db_error
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

    # Check if username contains only valid characters
    if not username.isalnum():
        return jsonify({"status": "error", "msg": "Invalid username format"}), 400

    logger.info(f"Login attempt for user: {username}")
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if admin exists and get password hash
        cursor.execute("""
            SELECT id, username, password_hash 
            FROM admins 
            WHERE username = %s
        """, (username,))
        admin = cursor.fetchone()
        
        if not admin:
            logger.warning(f"Login failed: User {username} not found")
            return jsonify({
                "status": "error",
                "msg": "Invalid username or password"
            }), 401

        # Verify password
        stored_hash = admin["password_hash"]
        if not scrypt.verify(password, stored_hash):
            logger.warning(f"Login failed: Invalid password for user {username}")
            return jsonify({
                "status": "error",
                "msg": "Invalid username or password"
            }), 401

        # Create token with additional claims
        access_token = create_access_token(
            identity=username,
            additional_claims={"admin_id": admin["id"]}
        )
        
        logger.info(f"Login successful for user: {username}")
        
        response = jsonify({
            "status": "success",
            "msg": "Login successful",
            "token": access_token,
            "username": username
        })
        
        # Set CORS headers
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Origin'] = '*'
        
        return response, 200
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        return jsonify({
            "status": "error",
            "msg": "An unexpected error occurred"
        }), 500
    finally:
        if conn:
            conn.close()

@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    blacklisted_tokens.add(jti)
    logger.info(f"User logged out successfully. Token blacklisted: {jti}")
    return jsonify({"status": "success", "msg": "Successfully logged out"}), 200

# --- Get all employees ---
@app.route("/employees", methods=["GET"])
@jwt_required()
def get_employees():
    try:
        current_user = get_jwt_identity()
        logger.info(f"User {current_user} requesting employee data")
        
        conn = get_db_connection()
        try:
            with conn.cursor(dictionary=True) as cursor:
                # First verify if the user exists in admins table
                cursor.execute("SELECT id FROM admins WHERE username = %s", (current_user,))
                admin = cursor.fetchone()
                
                if not admin:
                    logger.error(f"Unauthorized access attempt by user: {current_user}")
                    return jsonify({"msg": "Unauthorized access"}), 403
                
                # Get employee data
                cursor.execute("""
                    SELECT id, name, role, productivity, feedback, rating, 
                           created_at, updated_at 
                    FROM productivity 
                    ORDER BY name ASC
                """)
                
                employees = cursor.fetchall()
                
                # Convert datetime objects to strings for JSON serialization
                for emp in employees:
                    if 'created_at' in emp:
                        emp['created_at'] = emp['created_at'].isoformat() if emp['created_at'] else None
                    if 'updated_at' in emp:
                        emp['updated_at'] = emp['updated_at'].isoformat() if emp['updated_at'] else None
        finally:
            conn.close()
        
        logger.info(f"Successfully retrieved {len(employees)} employees")
        return jsonify({
            "status": "success",
            "count": len(employees),
            "employees": employees
        }), 200
        
    except mysql.connector.Error as db_err:
        logger.error(f"Database error while retrieving employees: {str(db_err)}")
        return jsonify({
            "status": "error",
            "msg": "Database error occurred",
            "error": str(db_err)
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error retrieving employees: {str(e)}")
        return jsonify({
            "status": "error",
            "msg": "An unexpected error occurred",
            "error": str(e)
        }), 500

# --- Update employee ---
@app.route("/employee/<int:emp_id>", methods=["PUT"])
@jwt_required()
def update_employee(emp_id):
    try:
        current_user = get_jwt_identity()
        logger.info(f"User {current_user} attempting to update employee {emp_id}")
        
        # Validate input data
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "msg": "No update data provided"
            }), 400
            
        # Extract and validate fields
        name = data.get("name")
        role = data.get("role")
        feedback = data.get("feedback")
        rating = data.get("rating")
        
        if not all([name, role]):  # These fields are required
            return jsonify({
                "status": "error",
                "msg": "Name and role are required fields"
            }), 400
            
        if rating is not None and (not isinstance(rating, (int, float)) or rating < 0 or rating > 5):
            return jsonify({
                "status": "error",
                "msg": "Rating must be between 0 and 5"
            }), 400
        
        conn = get_db_connection()
        try:
            with conn.cursor(dictionary=True) as cursor:
                # First check if the employee exists
                cursor.execute("SELECT id FROM productivity WHERE id = %s", (emp_id,))
                if not cursor.fetchone():
                    return jsonify({
                        "status": "error",
                        "msg": f"Employee with ID {emp_id} not found"
                    }), 404
                
                # Extract productivity if provided
                productivity = data.get("productivity")
                if productivity is not None:
                    if not isinstance(productivity, int) or productivity < 0 or productivity > 100:
                        return jsonify({
                            "status": "error",
                            "msg": "Productivity must be an integer between 0 and 100"
                        }), 400

                # Update the employee
                cursor.execute("""
                    UPDATE productivity
                    SET name=%s, role=%s, feedback=%s, rating=%s, 
                        productivity=COALESCE(%s, productivity),
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s
                """, (name, role, feedback, rating, productivity, emp_id))
                
                conn.commit()
                
                # Fetch the updated record
                cursor.execute("SELECT * FROM productivity WHERE id = %s", (emp_id,))
                updated_employee = cursor.fetchone()
        finally:
            conn.close()
        
        logger.info(f"Successfully updated employee {emp_id}")
        
        return jsonify({
            "status": "success",
            "msg": "Employee updated successfully",
            "employee": updated_employee
        }), 200
        
    except mysql.connector.Error as db_err:
        logger.error(f"Database error updating employee {emp_id}: {str(db_err)}")
        return jsonify({
            "status": "error",
            "msg": "Database error occurred",
            "error": str(db_err)
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error updating employee {emp_id}: {str(e)}")
        return jsonify({
            "status": "error",
            "msg": "An unexpected error occurred",
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)