CREATE DATABASE IF NOT EXISTS employee_db;
USE employee_db;

CREATE TABLE IF NOT EXISTS productivity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    role VARCHAR(100),
    productivity INT
);

INSERT INTO productivity (name, role, productivity) VALUES
('Kishore', 'Azure Cloud Developer', 90),
('Ravi', 'GCP Architect', 85),
('Sanjay', 'AWS Associate', 80);
