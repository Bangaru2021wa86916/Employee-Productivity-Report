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
from flask import send_file
import csv
from io import BytesIO, StringIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pyotp
import secrets# ----------------------------------------
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
# Helper: fetch admin row
def fetch_admin(username):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user
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

    user = fetch_admin(username)
    if not user or not pbkdf2_sha256.verify(password, user["password_hash"]):
        return jsonify({"msg": "Invalid username or password"}), 401

    # If MFA enabled -> ask for OTP (return a short-lived MFA-pending token)
    if user.get("mfa_enabled"):
        mfa_token = create_access_token(identity=username,
                                        additional_claims={"mfa": "pending"},
                                        expires_delta=datetime.timedelta(minutes=5))
        return jsonify({"mfa_required": True, "mfa_token": mfa_token}), 200

    # If MFA not enabled -> issue normal access token

    token = create_access_token(identity=username)
    return jsonify({"token": token}), 200

# ---------- MFA: Provision (returns secret & otpauth URI) ----------
# This endpoint allows the admin to create a secret (protected by username+password).
# The client should show the returned otpauth_uri as a QR for the authenticator app.
@app.route("/mfa/provision", methods=["POST"])
@limiter.limit("5 per minute")
def mfa_provision():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"msg": "Missing username/password"}), 400

    user = fetch_admin(username)
    if not user or not pbkdf2_sha256.verify(password, user["password_hash"]):
        return jsonify({"msg": "Invalid credentials"}), 401

    # Generate a new random secret
    secret = pyotp.random_base32()
    # Generate otpauth uri for QR codes (issuer and account name can be changed)
    issuer_name = "EmployeeProductivityApp"
    otpauth_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer_name)

    return jsonify({"secret": secret, "otpauth_uri": otpauth_uri}), 200

# ---------- MFA: Enable (confirm OTP and persist secret) ----------
@app.route("/mfa/enable", methods=["POST"])
@limiter.limit("5 per minute")
def mfa_enable():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    otp = data.get("otp")
    secret = data.get("secret")

    if not all([username, password, otp, secret]):
        return jsonify({"msg": "Missing fields (username, password, secret, otp required)"}), 400

    user = fetch_admin(username)
    if not user or not pbkdf2_sha256.verify(password, user["password_hash"]):
        return jsonify({"msg": "Invalid credentials"}), 401

    totp = pyotp.TOTP(secret)
    if not totp.verify(str(otp), valid_window=1):
        return jsonify({"msg": "Invalid OTP"}), 401

    # Persist secret and enable MFA
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE admins SET mfa_secret=%s, mfa_enabled=1 WHERE username=%s", (secret, username))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"msg": "MFA enabled successfully"}), 200

# ---------- MFA Validate (finalize login using mfa_token + otp) ----------
@app.route("/mfa/validate", methods=["POST"])
@limiter.limit("10 per minute")
@jwt_required()
def mfa_validate():
    # This endpoint expects the client to send the short-lived MFA token as Authorization header.
    # We check the JWT claim to ensure it was an MFA-pending token.
    jwt_payload = get_jwt()
    if jwt_payload.get("mfa") != "pending":
        return jsonify({"msg": "Invalid or expired MFA token"}), 401

    username = get_jwt_identity()
    data = request.get_json()
    otp = data.get("otp")
    if not otp:
        return jsonify({"msg": "Missing OTP"}), 400

    user = fetch_admin(username)
    if not user or not user.get("mfa_enabled") or not user.get("mfa_secret"):
        return jsonify({"msg": "MFA not configured for this user"}), 400

    totp = pyotp.TOTP(user["mfa_secret"])
    if not totp.verify(str(otp), valid_window=1):
        return jsonify({"msg": "Invalid OTP"}), 401

    # OTP valid — issue normal access token
    token = create_access_token(identity=username)
    return jsonify({"token": token}), 200

# ---------- MFA Disable (optional) ----------
@app.route("/mfa/disable", methods=["POST"])
@limiter.limit("5 per minute")
def mfa_disable():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    otp = data.get("otp")

    if not all([username, password, otp]):
        return jsonify({"msg": "Missing username, password or otp"}), 400

    user = fetch_admin(username)
    if not user or not pbkdf2_sha256.verify(password, user["password_hash"]):
        return jsonify({"msg": "Invalid credentials"}), 401

    if not user.get("mfa_enabled") or not user.get("mfa_secret"):
        return jsonify({"msg": "MFA not enabled for this account"}), 400

    totp = pyotp.TOTP(user["mfa_secret"])
    if not totp.verify(str(otp), valid_window=1):
        return jsonify({"msg": "Invalid OTP"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE admins SET mfa_secret=NULL, mfa_enabled=0 WHERE username=%s", (username,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"msg": "MFA disabled successfully"}), 200

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

# ---------- DELETE EMPLOYEE ----------
@app.route("/employee/<int:emp_id>", methods=["DELETE"])
@jwt_required()
def delete_employee(emp_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productivity WHERE id=%s", (emp_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"msg": "Employee deleted successfully"}), 200



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

# ---------- EXPORT CSV ----------
@app.route("/export/csv", methods=["GET"])
@jwt_required()
def export_csv():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productivity ORDER BY id ASC")
    employees = cursor.fetchall()
    cursor.close()
    conn.close()

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=employees[0].keys())
    writer.writeheader()
    writer.writerows(employees)
    output.seek(0)

    return send_file(
        BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='employee_report.csv'
    )


# ---------- EXPORT PDF ----------
@app.route("/export/pdf", methods=["GET"])
@jwt_required()
def export_pdf():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productivity ORDER BY id ASC")
    employees = cursor.fetchall()
    cursor.close()
    conn.close()

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, height - 50, "Employee Productivity Report")

    pdf.setFont("Helvetica", 10)
    y = height - 100
    pdf.drawString(50, y, "ID")
    pdf.drawString(100, y, "Name")
    pdf.drawString(250, y, "Role")
    pdf.drawString(400, y, "Prod(%)")
    pdf.drawString(470, y, "Rating")
    y -= 20

    for emp in employees:
        if y < 50:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 10)
        pdf.drawString(50, y, str(emp["id"]))
        pdf.drawString(100, y, emp["name"][:20])
        pdf.drawString(250, y, emp["role"][:25])
        pdf.drawString(400, y, str(emp["productivity"]))
        pdf.drawString(470, y, str(emp["rating"] or "-"))
        y -= 20

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="employee_report.pdf",
        mimetype="application/pdf"
    )

# ---------- MAIN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)