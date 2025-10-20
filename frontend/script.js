<script>
    let token = '';

    async function login() {
      const username = document.getElementById("username").value;
      const password = document.getElementById("password").value;

      const res = await fetch("http://localhost:5000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });

      if (res.ok) {
        const data = await res.json();
        token = data.token;
        document.getElementById("login-section").style.display = "none";
        document.getElementById("employee-section").style.display = "block";
        loadEmployees();
      } else {
        alert("Invalid login");
      }
    }

    async function loadEmployees() {
      const res = await fetch("http://localhost:5000/employees", {
        headers: { "Authorization": "Bearer " + token }
      });
      const data = await res.json();

      const table = document.getElementById("employee-table");
      table.innerHTML = '';
      data.forEach(emp => {
        table.innerHTML += `
          <tr>
            <td>${emp.id}</td>
            <td><input value="${emp.name}" id="name-${emp.id}"></td>
            <td><input value="${emp.role}" id="role-${emp.id}"></td>
            <td><input value="${emp.feedback}" id="feedback-${emp.id}"></td>
            <td><input value="${emp.rating}" id="rating-${emp.id}" type="number" step="0.1"></td>
            <td><button onclick="updateEmployee(${emp.id})">Save</button></td>
          </tr>`;
      });
    }

    async function updateEmployee(id) {
      const name = document.getElementById(`name-${id}`).value;
      const role = document.getElementById(`role-${id}`).value;
      const feedback = document.getElementById(`feedback-${id}`).value;
      const rating = parseFloat(document.getElementById(`rating-${id}`).value);

      const res = await fetch(`http://localhost:5000/employee/${id}`, {
        method: "PUT",
        headers: {
          "Authorization": "Bearer " + token,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ name, role, feedback, rating })
      });

      if (res.ok) {
        alert("Employee updated successfully!");
        loadEmployees();
      } else {
        alert("Failed to update employee");
      }
    }
  </script>