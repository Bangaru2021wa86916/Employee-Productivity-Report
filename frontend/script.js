const backendURL = "http://localhost:5000";

function getReport() {
  const name = document.getElementById("nameInput").value;
  fetch(`${backendURL}/report?name=${name}`)
    .then(res => res.json())
    .then(data => {
      const report = document.getElementById("report");
      if (data.length === 0) {
        report.innerHTML = "No report found.";
      } else {
        const emp = data[0];
        report.innerHTML = `
          <h3>Report for ${emp.name}</h3>
          <p><strong>Role:</strong> ${emp.role}</p>
          <p><strong>Productivity:</strong> ${emp.productivity}%</p>
        `;
      }
    });
}


function addEmployee() {
  const name = document.getElementById("addName").value;
  const role = document.getElementById("addRole").value;
  const productivity = document.getElementById("addProd").value;
  fetch(`${backendURL}/add`, {
    method: "POST",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, role, productivity })  // Use object, not array
  }).then(res => res.json()).then(data => alert(data.message));
}


function deleteEmployee() {
  const name = document.getElementById("delName").value;
  fetch(`${backendURL}/delete`, {
    method: "POST",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name })
  }).then(res => res.json()).then(data => alert(data.message));
}
async function loadEmployees() {
  try {
    const res = await fetch(`${API_URL}/employees`, {
      headers: { 
        "Authorization": `Bearer ${token}`,
        "Accept": "application/json"
      }
    });
    if (!res.ok) {
      if (res.status === 401) {
        alert("Session expired. Please log in again.");
        location.reload();
        return;
      }     throw new Error(`HTTP error! status: ${res.status}`);
    }

    const data = await res.json();
    const table = document.getElementById("employee-table");
    table.innerHTML = '';
    if (!data.employees || !Array.isArray(data.employees)) {
      console.error("Invalid data format received:", data);
      alert("Error: Invalid data format received from server");
      return;
    }
    data.employees.forEach(emp => {
      table.innerHTML += `
        <tr>
            <td>${emp.id}</td>
            <td><input value="${emp.name || ''}" id="name-${emp.id}"></td>
            <td><input value="${emp.role || ''}" id="role-${emp.id}"></td>
            <td><input value="${emp.feedback || ''}" id="feedback-${emp.id}"></td>
            <td><input value="${emp.rating || ''}" id="rating-${emp.id}" type="number" step="0.1" min="0" max="5"></td>
            <td><button onclick="updateEmployee(${emp.id})">Save</button></td>
        </tr>`;
    });
    } catch (err) {
    console.error("Load error:", err);
    alert("Could not fetch employee data. Please check the console for details.");
  }
}

async function updateEmployee(id) {
  const name = document.getElementById(`name-${id}`).value;
  const role = document.getElementById(`role-${id}`).value;
  const feedback = document.getElementById(`feedback-${id}`).value;
  const rating = parseFloat(document.getElementById(`rating-${id}`).value);
    try {
    const res = await fetch(`${API_URL}/employee/${id}`, {
      method: "PUT",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify({ name, role, feedback, rating })
    });
    if (!res.ok) {
        if (res.status === 401) {
            alert("Session expired. Please log in again.");
            location.reload();
            return;
        }
        throw new Error(`HTTP error! status: ${res.status}`);
    }
    alert("Employee updated successfully.");
  }
    catch (err) {
    console.error("Update error:", err);
    alert("Could not update employee data. Please check the console for details.");
  }
}