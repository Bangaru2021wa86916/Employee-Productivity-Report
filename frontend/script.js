// Correct backend endpoint (inside Docker network)
const backendURL = "http://backend:5000"; 

let token = "";

// --- Login Function ---
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
      document.getElementById("login-section").style.display = "none";
      document.getElementById("employee-section").style.display = "block";
      loadEmployees();
    } else {
      alert(data.message || "Invalid login credentials");
    }
  } catch (err) {
    console.error(err);
    alert("Error connecting to backend.");
  }
}

// --- Load Employees ---
async function loadEmployees() {
  try {
    const res = await fetch(`${"http://backend:5000/report"}/employees`, {
      headers: { "Authorization": `Bearer ${token}` }
    });
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
          <td><textarea id="feedback-${emp.id}">${emp.feedback || ''}</textarea></td>
          <td>${emp.last_updated}</td>
          <td>
            <button class="save-btn" onclick="updateEmployee(${emp.id})">Save</button>
            <button class="delete-btn" onclick="deleteEmployee(${emp.id})">Delete</button>
          </td>
        </tr>
      `;
    });
  } catch (err) {
    console.error("Error loading employees:", err);
    alert("Failed to fetch employee data");
  }
}

// --- Add Employee ---
async function addEmployee() {
  const name = document.getElementById("addName").value;
  const role = document.getElementById("addRole").value;
  const productivity = parseFloat(document.getElementById("addProd").value);

  try {
    const res = await fetch(`${backendURL}/add`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ name, role, productivity })
    });

    const data = await res.json();
    alert(data.message);
    loadEmployees();
  } catch (err) {
    console.error("Add error:", err);
    alert("Could not add employee");
  }
}

// --- Update Employee ---
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
    alert(data.message);
    loadEmployees();
  } catch (err) {
    console.error("Update error:", err);
    alert("Update failed");
  }
}

// --- Delete Employee ---
async function deleteEmployee(id) {
  if (!confirm("Are you sure you want to delete this employee?")) return;

  try {
    const res = await fetch(`${backendURL}/employee/${id}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${token}` }
    });

    const data = await res.json();
    alert(data.message);
    loadEmployees();
  } catch (err) {
    console.error("Delete error:", err);
    alert("Failed to delete employee");
  }
}

function showAddForm() {
  document.getElementById("add-form").style.display = "block";
}
