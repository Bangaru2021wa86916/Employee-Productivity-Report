const backendURL = "http://localhost:5000";
let token = "";

// LOGIN
async function login() {
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  const res = await fetch(`${backendURL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  const data = await res.json();
  if (res.ok) {
    token = data.access_token;
    document.getElementById("login-section").style.display = "none";
    document.getElementById("employee-section").style.display = "block";
    loadEmployees();
  } else {
    alert(data.msg || "Login failed");
  }
}

// LOAD EMPLOYEES
async function loadEmployees() {
  const res = await fetch(`${backendURL}/employees`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  const tbody = document.querySelector("#employee-table tbody");
  tbody.innerHTML = "";

  if (data.employees) {
    data.employees.forEach((emp) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${emp.id}</td>
        <td>${emp.name}</td>
        <td>${emp.role}</td>
        <td>${emp.productivity}%</td>
        <td>${emp.rating}</td>
        <td>${emp.feedback}</td>
        <td>${emp.updated_at || ""}</td>
      `;
      tbody.appendChild(row);
    });
  }
}

// ADD EMPLOYEE (example only)
function addEmployee() {
  alert("Add employee feature not implemented in this example.");
}

// DELETE EMPLOYEE
async function deleteEmployee() {
  const name = document.getElementById("deleteName").value.trim();
  if (!name) return alert("Enter employee name to delete");

  if (!confirm(`Delete employee: ${name}?`)) return;

  const res = await fetch(`${backendURL}/employee?name=${encodeURIComponent(name)}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (res.ok) {
    alert(data.msg);
    loadEmployees();
  } else {
    alert(data.msg || "Delete failed");
  }
}

// LOGOUT
async function logout() {
  const res = await fetch(`${backendURL}/logout`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.ok) {
    token = "";
    document.getElementById("login-section").style.display = "block";
    document.getElementById("employee-section").style.display = "none";
    alert("Logged out successfully");
  } else {
    alert("Logout failed");
  }
}

// DOWNLOAD CSV
function downloadCSV() {
  const rows = [["ID", "Name", "Role", "Productivity", "Rating", "Feedback", "Last Updated"]];
  const table = document.querySelectorAll("#employee-table tr");
  for (const tr of table) {
    const cells = Array.from(tr.children).map((td) => td.innerText);
    if (cells.length === 7) rows.push(cells);
  }
  const csv = rows.map((r) => r.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "employee_report.csv";
  a.click();
}

// DOWNLOAD PDF
function downloadPDF() {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();
  doc.text("Employee Productivity Report", 14, 14);

  let y = 24;
  const rows = document.querySelectorAll("#employee-table tr");
  rows.forEach((r) => {
    const text = Array.from(r.children).map((td) => td.innerText).join(" | ");
    doc.text(text, 10, y);
    y += 8;
    if (y > 280) {
      doc.addPage();
      y = 20;
    }
  });

  doc.save("employee_report.pdf");
}
