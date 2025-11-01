const backendURL = "http://localhost:5000";
let token = localStorage.getItem("token") || "";

// Auto-login if token exists
window.onload = () => {
  if (token) {
    document.getElementById("login-section").style.display = "none";
    document.getElementById("employee-section").style.display = "block";
    loadEmployees();
  }
};

async function login() {
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  try {
    const res = await fetch(`${backendURL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    const data = await res.json();
    if (res.ok && data.token) {
      token = data.token;
      localStorage.setItem("token", token); // ✅ store token
      document.getElementById("login-section").style.display = "none";
      document.getElementById("employee-section").style.display = "block";
      loadEmployees();
    } else {
      alert(data.msg || "Login failed");
    }
  } catch (err) {
    alert("Error connecting to backend");
    console.error(err);
  }
}

async function addEmployee() {
  const name = prompt("Enter employee name:");
  const role = prompt("Enter employee role:");
  const productivity = parseInt(prompt("Enter productivity (0–100):"));
  const feedback = prompt("Enter feedback:");
  const rating = parseFloat(prompt("Enter rating (0–5):"));

  try {
    const res = await fetch(`${backendURL}/add`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ name, role, productivity, feedback, rating })
    });

    const data = await res.json();
    alert(data.msg);
    loadEmployees(); // reload table
  } catch (err) {
    alert("Failed to add employee");
    console.error(err);
  }
}

async function loadEmployees() {
  try {
    const res = await fetch(`${backendURL}/employees`, {
      headers: { "Authorization": `Bearer ${token}` }
    });

    if (res.status === 401) {
      // token expired or invalid
      localStorage.removeItem("token");
      token = "";
      document.getElementById("employee-section").style.display = "none";
      document.getElementById("login-section").style.display = "block";
      alert("Session expired. Please login again.");
      return;
    }

    const data = await res.json();
    const table = document.getElementById("employee-table");
    table.innerHTML = "";

    data.employees.forEach(emp => {
      table.innerHTML += `
        <tr>
          <td>${emp.id}</td>
          <td><input value="${emp.name}" id="name-${emp.id}"></td>
          <td><input value="${emp.role}" id="role-${emp.id}"></td>
          <td>${emp.productivity}%</td>
          <td>${emp.rating || '-'}</td>
          <td>
            <textarea id="feedback-${emp.id}" onclick="openFeedbackTab(${emp.id})" readonly>${emp.feedback || ''}</textarea>
          </td>
          <td>${emp.updated_at}</td>
          <td>
            <button onclick="updateEmployee(${emp.id})">Save</button>
            <button style="background:#dc3545;color:white;border:none;padding:4px 8px;border-radius:4px;cursor:pointer;" onclick="deleteEmployee(${emp.id})">Delete</button>
          </td>
        </tr>
      `;
    });
  } catch (err) {
    alert("Failed to load employees");
    console.error(err);
  }
}

async function updateEmployee(id) {
  const name = document.getElementById(`name-${id}`).value;
  const role = document.getElementById(`role-${id}`).value;
  const feedback = document.getElementById(`feedback-${id}`).value;
  const rating = parseFloat(prompt("Enter rating (0–5):"));

  try {
    const res = await fetch(`${backendURL}/employee/${id}`, {
      method: "PUT",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ name, role, feedback, rating })
    });

    const data = await res.json();
    alert(data.msg);
    loadEmployees();
  } catch (err) {
    alert("Update failed");
    console.error(err);
  }
}

async function deleteEmployee(id) {
  if (!confirm("Are you sure you want to delete this employee?")) return;

  try {
    const res = await fetch(`${backendURL}/employee/${id}`, {
      method: "DELETE",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      }
    });

    const data = await res.json();
    alert(data.msg);
    loadEmployees();
  } catch (err) {
    alert("Failed to delete employee");
    console.error(err);
  }
}

async function downloadPDF() {
  try {
    const res = await fetch(`${backendURL}/export/pdf`, {
      method: "GET",
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Failed to download PDF");
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "employee_report.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
  } catch (err) {
    alert("Error downloading PDF");
    console.error(err);
  }
}

async function downloadCSV() {
  try {
    const res = await fetch(`${backendURL}/export/csv`, {
      method: "GET",
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Failed to download CSV");
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "employee_report.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
  } catch (err) {
    alert("Error downloading CSV");
    console.error(err);
  }
}

async function logout() {
  if (!confirm("Are you sure you want to logout?")) return;
  try {
    const res = await fetch(`${backendURL}/logout`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` }
    });
    const data = await res.json();
    alert(data.msg || "Logged out successfully");
  } catch (err) {
    console.error(err);
  } finally {
    localStorage.removeItem("token");
    token = "";
    document.getElementById("employee-section").style.display = "none";
    document.getElementById("login-section").style.display = "block";
  }
}
function togglePassword() {
    const passwordField = document.getElementById("password");
    const toggleIcon = document.querySelector(".toggle-password");

    if (passwordField.type === "password") {
        passwordField.type = "text";
        toggleIcon.textContent = "🧑‍💻";
        toggleIcon.style.color = "#007bff";
        toggleIcon.style.transform = "rotate(10deg)";
    } else {
        passwordField.type = "password";
        toggleIcon.textContent = "👁️";
        toggleIcon.style.color = "#555";
        toggleIcon.style.transform = "rotate(0deg)";
    }
}

function openFeedbackTab(empId) {
  // Get feedback text from main table
  const feedbackText = document.getElementById(`feedback-${empId}`).value;
  const empName = document.getElementById(`name-${empId}`).value;
  const empRole = document.getElementById(`role-${empId}`).value;

  // Open new tab (same origin)
  const feedbackWindow = window.open("", "_blank");

  // Write editable feedback view
  feedbackWindow.document.write(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Feedback - ${empName}</title>
      <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>👨‍💼</text></svg>">
      <style>
        body {
          font-family: 'Segoe UI', Arial, sans-serif;
          background: #f7f9fb;
          padding: 2rem;
        }
        h2 {
          color: #2c3e50;
          text-align: center;
        }
        textarea {
          width: 100%;
          height: 300px;
          padding: 1rem;
          border-radius: 8px;
          border: 1px solid #ccc;
          font-size: 1rem;
          margin-top: 1rem;
          box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }
        button {
          background: linear-gradient(135deg, #007bff, #00c6ff);
          color: white;
          padding: 0.8rem 1.5rem;
          border: none;
          border-radius: 8px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          box-shadow: 0 3px 6px rgba(0,0,0,0.2);
          margin-top: 1rem;
          transition: all 0.3s ease;
        }
        button:hover {
          background: linear-gradient(135deg, #339af0, #0072ff);
          transform: translateY(-2px);
        }
        .container {
          max-width: 700px;
          margin: 0 auto;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h2>Feedback for ${empName} (${empRole})</h2>
        <textarea id="feedbackEdit">${feedbackText}</textarea>
        <button onclick="saveFeedback()">💾 Save Feedback</button>
      </div>

      <script>
        async function saveFeedback() {
    const feedback = document.getElementById("feedback").value.trim();
    const employeeId = localStorage.getItem("employee_id"); // or from a dropdown/input
    const projectId = localStorage.getItem("project_id");   // or from context

    if (!feedback || !employeeId || !projectId) {
        alert("Please fill all required fields before submitting.");
        return;
    }

    const token = localStorage.getItem("token");

    const response = await fetch("http://localhost:5000/feedback", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({
            feedback: feedback,
            employee_id: employeeId,
            project_id: projectId
        })
    });

    const data = await response.json();
    if (response.ok) {
        alert("Feedback saved successfully!");
    } else {
        alert(data.msg || "Error saving feedback.");
    }
}

      </script>
    </body>
    </html>
  `);
}
