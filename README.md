# Employee Productivity Report System

A containerized full-stack web application designed to streamline employee roster management, performance feedback tracking, and automated productivity reporting. Built as an M.Tech Dissertation Project at BITS Pilani.

---

## Architecture Overview

The application follows a multi-tier containerized architecture orchestrated via Docker:
* **Frontend / Reverse Proxy (`Nginx` + `JavaScript`):** Serves the single-page administrator dashboard (`script.js`) and routes API requests to the backend.
* **Backend API (`Python` / `Flask`):** Handles RESTful endpoints (`app.py`), JWT-based administrator authentication, report generation (PDF/CSV), and MySQL connection pooling.
* **Database (`MySQL`):** Stores administrator credentials, employee records, productivity metrics, and feedback logs initialized via `init.sql`.

---

## Key Features

* **Secure Admin Authentication:** JWT-based login, logout, and session validation protecting administrative endpoints.
* **Employee Roster Management:** Full CRUD (Create, Read, Update, Delete) operations for managing employee profiles and records.
* **Productivity & Feedback Tracking:** Dedicated feedback and rating editor to log performance reviews and operational metrics.
* **Automated Report Exports:** One-click generation and download of structured productivity reports in **PDF** and **CSV** formats.
* **Database Connection Pooling:** Backend connection pooling in Flask to handle concurrent queries efficiently and reduce connection overhead.

---

## Tech Stack

* **Backend:** Python 3, Flask, REST APIs, PyJWT
* **Frontend:** HTML5, CSS3, Vanilla JavaScript (`script.js`)
* **Database:** MySQL (with SQL Connection Pooling)
* **Infrastructure & DevOps:** Docker, Docker Compose, Nginx
* **API Testing:** Postman

---

## Project Structure

```text
employee-productivity-report/
├── backend/
│   ├── app.py              # Flask REST API routes, JWT auth, and connection pool
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend container build instructions
├── frontend/
│   ├── index.html          # Admin dashboard UI
│   ├── script.js           # Frontend logic & API integration
│   └── nginx.conf          # Reverse proxy configuration
├── database/
│   └── init.sql            # Database schema and initial seed data
├── docker-compose.yml      # Multi-container orchestration & networking
└── README.md
