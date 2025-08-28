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
