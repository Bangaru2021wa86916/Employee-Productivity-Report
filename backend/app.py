from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_cors import CORS
import datetime

app = Flask(__name__)
CORS(app)

# Secret key for JWT
app.config["JWT_SECRET_KEY"] = "super-secret-key"  # change this in production
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=1)
jwt = JWTManager(app)

# Admin credentials (you can move this to DB later)
admins = {
    "admin": "admin123"
}

# Sample employee data
employees = [
    {"id": 1, "name": "Kishore", "role": "Azure Cloud Developer", "feedback": "Excellent", "rating": 4.7},
    {"id": 2, "name": "Ravi", "role": "GCP Architect", "feedback": "Good work", "rating": 4.4},
    {"id": 3, "name": "Sanjay", "role": "AWS Associate", "feedback": "Improving", "rating": 4.1}
]

# --- ADMIN LOGIN (JWT Authentication) ---
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username in admins and admins[username] == password:
        access_token = create_access_token(identity=username)
        return jsonify({"token": access_token}), 200
    return jsonify({"msg": "Invalid credentials"}), 401


# --- GET EMPLOYEES ---
@app.route("/employees", methods=["GET"])
@jwt_required()
def get_employees():
    return jsonify(employees)


# --- UPDATE EMPLOYEE ---
@app.route("/employee/<int:emp_id>", methods=["PUT"])
@jwt_required()
def update_employee(emp_id):
    data = request.get_json()
    for emp in employees:
        if emp["id"] == emp_id:
            emp.update({
                "name": data.get("name", emp["name"]),
                "role": data.get("role", emp["role"]),
                "feedback": data.get("feedback", emp["feedback"]),
                "rating": data.get("rating", emp["rating"])
            })
            return jsonify({"msg": "Employee updated successfully", "employee": emp}), 200
    return jsonify({"msg": "Employee not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)