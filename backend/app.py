from flask import Flask, request, jsonify, Response, render_template
import mysql.connector
from flask_cors import CORS
import csv
import io
import pdfkit

app = Flask(__name__)
CORS(app)

def get_connection():
    return mysql.connector.connect(
        host="db",          # 'db' must match the service name in docker-compose.yml
        user="root",
        password="password",
        database="employee_db"
    )

@app.route('/report', methods=['GET'])
def get_report():
    name = request.args.get('name')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productivity WHERE name = %s", (name,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

@app.route('/add', methods=['POST'])
def add_employee():
    data = request.json
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO productivity (name, role, productivity) VALUES (%s, %s, %s)",
        (data['name'], data['role'], data['productivity'])
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Employee added successfully'})

@app.route('/delete', methods=['POST'])
def delete_employee():
    data = request.json
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productivity WHERE name = %s", (data['name'],))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Employee deleted successfully'})

@app.route('/download/csv')
def download_csv():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productivity")
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Role', 'Productivity'])
    writer.writerows(rows)
    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=productivity_report.csv"}
    )

@app.route('/download/pdf')
def download_pdf():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productivity")
    rows = cursor.fetchall()
    conn.close()

    # Convert data into simple HTML for PDF
    html_content = "<h1>Employee Productivity Report</h1><table border='1'><tr><th>Name</th><th>Role</th><th>Productivity</th></tr>"
    for row in rows:
        html_content += f"<tr><td>{row['name']}</td><td>{row['role']}</td><td>{row['productivity']}</td></tr>"
    html_content += "</table>"

    pdf = pdfkit.from_string(html_content, False)
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment;filename=productivity_report.pdf"}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
