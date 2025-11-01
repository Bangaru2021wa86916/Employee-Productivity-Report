// frontend/script.js
const backendURL = "http://localhost:5000";
let token = "";

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
    if (res.ok && data.access_token) {
      token = data.access_token;
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
    alert(data.msg || "Added");
    loadEmployees();
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
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.msg || 'Error');
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
          <td><textarea id="feedback-${emp.id}">${emp.feedback || ''}</textarea></td>
          <td>${emp.updated_at}</td>
          <td><button onclick="updateEmployee(${emp.id})">Save</button></td>
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
    alert(data.msg || "Updated");
    loadEmployees();
  } catch (err) {
    alert("Update failed");
    console.error(err);
  }
}