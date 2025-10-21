from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_cors import CORS
from werkzeug.security import check_password_hash
import mysql.connector
import datetime

app = Flask(__name__)
CORS(app)

# JWT setup
app.config["JWT_SECRET_KEY"] = "super-secret-key"  # change in production
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=1)
jwt = JWTManager(app)

# --- Database connection ---
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",          # change if different
        password="",          # your MySQL password here
        database="employee_db"
    )

# --- Admin Login ---
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
    admin = cursor.fetchone()
    cursor.close()
    conn.close()

    if admin and check_password_hash(admin["password_hash"], password):
        access_token = create_access_token(identity=username)
        return jsonify({"token": access_token}), 200

    return jsonify({"msg": "Invalid username or password"}), 401


# --- Get all employees ---
@app.route("/employees", methods=["GET"])
@jwt_required()
def get_employees():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productivity")
    employees = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(employees), 200


# --- Update employee ---
@app.route("/employee/<int:emp_id>", methods=["PUT"])
@jwt_required()
def update_employee(emp_id):
    data = request.get_json()
    name = data.get("name")
    role = data.get("role")
    feedback = data.get("feedback")
    rating = data.get("rating")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE productivity
        SET name=%s, role=%s, feedback=%s, rating=%s
        WHERE id=%s
    """, (name, role, feedback, rating, emp_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"msg": "Employee updated successfully"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
