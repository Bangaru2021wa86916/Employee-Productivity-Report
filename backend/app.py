from flask import Flask, request, jsonify
from flask_cors import CORS
CORS(app)
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import mysql.connector
import datetime

app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = "your_secret_key"
jwt = JWTManager(app)

# ---------- DATABASE CONNECTION ----------
def get_db_connection():
    return mysql.connector.connect(
        host="db",
        user="root",
        password="root",
        database="employee_db"
    )

# ---------- LOGIN ----------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username == "admin" and password == "admin123":
        access_token = create_access_token(identity={"username": username})
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Invalid credentials"}), 401


# ---------- GET EMPLOYEES ----------
@app.route("/employees", methods=["GET"])
@jwt_required()
def get_employees():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productivity")
    employees = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"employees": employees}), 200


# ---------- UPDATE EMPLOYEE ----------
@app.route("/employee/<int:emp_id>", methods=["PUT"])
@jwt_required()
def update_employee(emp_id):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE productivity
           SET name=%s, role=%s, productivity=%s, rating=%s, feedback=%s
           WHERE id=%s""",
        (data["name"], data["role"], data["productivity"], data["rating"], data["feedback"], emp_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"msg": "Employee updated successfully"}), 200


# ---------- DELETE EMPLOYEE BY NAME ----------
@app.route("/employee", methods=["DELETE"])
@jwt_required()
def delete_employee():
    name = request.args.get("name")
    if not name:
        return jsonify({"msg": "Name parameter is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM productivity WHERE name = %s", (name,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"msg": "No employee found with given name"}), 404
        return jsonify({"msg": f"Employee '{name}' deleted successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"msg": "Delete failed", "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ---------- LOGOUT ----------
@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    return jsonify({"msg": "Logout successful"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
