const API_BASE = "http://localhost:5000";

async function fetchAll() {
  const res = await fetch(`${API_BASE}/report?name=%`);
  const data = await res.json();
  const tbody = document.querySelector("#reportTable tbody");
  tbody.innerHTML = "";
  data.forEach(emp => {
    const row = `<tr><td>${emp.name}</td><td>${emp.role}</td><td>${emp.productivity}</td></tr>`;
    tbody.innerHTML += row;
  });
}

async function addEmployee() {
  const name = document.getElementById("name").value;
  const role = document.getElementById("role").value;
  const productivity = document.getElementById("productivity").value;

  await fetch(`${API_BASE}/add`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, role, productivity })
  });

  alert("Employee added!");
  fetchAll();
}

async function deleteEmployee() {
  const name = document.getElementById("name").value;
  await fetch(`${API_BASE}/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name })
  });
  alert("Employee deleted!");
  fetchAll();
}

function downloadCSV() {
  window.open(`${API_BASE}/download/csv`, "_blank");
}

function downloadPDF() {
  window.open(`${API_BASE}/download/pdf`, "_blank");
}
