-- ============================================================
-- Biometric Attendance Management & Payroll System
-- Database Schema - MySQL
-- ============================================================

CREATE DATABASE IF NOT EXISTS biometric_attendance;
USE biometric_attendance;

-- Admin Users
CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,  -- SHA256 hash
    full_name VARCHAR(100),
    role ENUM('admin', 'hr', 'viewer') DEFAULT 'hr',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Employees
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    department VARCHAR(50),
    designation VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(15),
    salary DECIMAL(10,2) DEFAULT 0.00,
    join_date DATE,
    fingerprint_hash VARCHAR(255) DEFAULT '',
    face_encoding VARCHAR(500) DEFAULT '',
    status ENUM('active','inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Attendance
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id VARCHAR(20) NOT NULL,
    att_date DATE NOT NULL,
    check_in TIME,
    check_out TIME,
    hours_worked DECIMAL(5,2) DEFAULT 0,
    method ENUM('fingerprint','face','manual') DEFAULT 'manual',
    status ENUM('present','absent','half_day','leave') DEFAULT 'present',
    notes TEXT,
    UNIQUE KEY unique_att (emp_id, att_date),
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE
);

-- Payroll
CREATE TABLE IF NOT EXISTS payroll (
    id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id VARCHAR(20) NOT NULL,
    month INT NOT NULL,
    year INT NOT NULL,
    present_days INT DEFAULT 0,
    absent_days INT DEFAULT 0,
    half_days INT DEFAULT 0,
    basic_salary DECIMAL(10,2) DEFAULT 0,
    hra DECIMAL(10,2) DEFAULT 0,
    da DECIMAL(10,2) DEFAULT 0,
    pf DECIMAL(10,2) DEFAULT 0,
    tax DECIMAL(10,2) DEFAULT 0,
    gross_salary DECIMAL(10,2) DEFAULT 0,
    deductions DECIMAL(10,2) DEFAULT 0,
    net_salary DECIMAL(10,2) DEFAULT 0,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_pay (emp_id, month, year),
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE
);

-- ─── Seed Data ────────────────────────────────────────────────────────────────

-- Default Admin (password: admin123)
INSERT IGNORE INTO admin_users (username, password, full_name, role)
VALUES ('admin', SHA2('admin123', 256), 'System Admin', 'admin');

-- Default HR (password: hr123)
INSERT IGNORE INTO admin_users (username, password, full_name, role)
VALUES ('hr', SHA2('hr123', 256), 'HR Manager', 'hr');

-- Sample Employees
INSERT IGNORE INTO employees (emp_id, full_name, department, designation, email, phone, salary, join_date, fingerprint_hash)
VALUES 
('EMP001', 'Dr. Ramesh Kumar', 'Computer Science', 'Professor', 'ramesh@college.edu', '9876543210', 85000.00, '2018-06-01', SHA2('FP_EMP001', 256)),
('EMP002', 'Prof. Priya Sharma', 'Mathematics', 'Associate Professor', 'priya@college.edu', '9876543211', 72000.00, '2019-07-15', SHA2('FP_EMP002', 256)),
('EMP003', 'Mr. Arjun Nair', 'Physics', 'Assistant Professor', 'arjun@college.edu', '9876543212', 58000.00, '2020-01-10', SHA2('FP_EMP003', 256)),
('EMP004', 'Ms. Kavitha Reddy', 'Electronics', 'Lecturer', 'kavitha@college.edu', '9876543213', 48000.00, '2021-06-01', SHA2('FP_EMP004', 256)),
('EMP005', 'Mr. Suresh Rao', 'Administration', 'Administrative Officer', 'suresh@college.edu', '9876543214', 42000.00, '2017-03-20', SHA2('FP_EMP005', 256)),
('EMP006', 'Ms. Anitha Menon', 'Library', 'Librarian', 'anitha@college.edu', '9876543215', 38000.00, '2016-08-05', SHA2('FP_EMP006', 256)),
('EMP007', 'Dr. Vikram Singh', 'Computer Science', 'HOD & Professor', 'vikram@college.edu', '9876543216', 95000.00, '2015-01-01', SHA2('FP_EMP007', 256)),
('EMP008', 'Prof. Meena Iyer', 'Chemistry', 'Associate Professor', 'meena@college.edu', '9876543217', 70000.00, '2019-11-20', SHA2('FP_EMP008', 256));

-- Sample Attendance (current month)
SET @today = CURDATE();
SET @month = MONTH(CURDATE());
SET @year = YEAR(CURDATE());

INSERT IGNORE INTO attendance (emp_id, att_date, check_in, check_out, hours_worked, method, status)
VALUES 
('EMP001', @today, '09:00:00', '17:00:00', 8.00, 'fingerprint', 'present'),
('EMP002', @today, '09:15:00', '17:10:00', 7.92, 'face', 'present'),
('EMP003', @today, '09:05:00', '17:00:00', 7.92, 'fingerprint', 'present'),
('EMP007', @today, '08:50:00', '17:30:00', 8.67, 'fingerprint', 'present');

USE biometric_attendance;

-- Get current year and month
SET @yr = YEAR(CURDATE());
SET @mo = MONTH(CURDATE());

-- Add attendance for past days this month
INSERT IGNORE INTO attendance (emp_id, att_date, check_in, check_out, hours_worked, method, status)
VALUES
-- EMP001
('EMP001', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-01'), '09:00:00', '17:00:00', 8.00, 'fingerprint', 'present'),
('EMP001', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-02'), '09:05:00', '17:00:00', 7.92, 'fingerprint', 'present'),
('EMP001', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-03'), '09:10:00', '17:00:00', 7.83, 'fingerprint', 'present'),
('EMP001', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-04'), NULL, NULL, 0, 'manual', 'absent'),
('EMP001', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-05'), '09:00:00', '17:00:00', 8.00, 'fingerprint', 'present'),

-- EMP002
('EMP002', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-01'), '09:15:00', '17:10:00', 7.92, 'face', 'present'),
('EMP002', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-02'), '09:20:00', '17:00:00', 7.67, 'face', 'present'),
('EMP002', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-03'), NULL, NULL, 0, 'manual', 'absent'),
('EMP002', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-04'), '09:00:00', '13:00:00', 4.00, 'face', 'half_day'),
('EMP002', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-05'), '09:15:00', '17:00:00', 7.75, 'face', 'present'),

-- EMP003
('EMP003', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-01'), '09:05:00', '17:00:00', 7.92, 'fingerprint', 'present'),
('EMP003', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-02'), '09:00:00', '17:00:00', 8.00, 'fingerprint', 'present'),
('EMP003', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-03'), '09:10:00', '17:00:00', 7.83, 'fingerprint', 'present'),
('EMP003', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-04'), '09:00:00', '17:00:00', 8.00, 'fingerprint', 'present'),
('EMP003', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-05'), NULL, NULL, 0, 'manual', 'absent'),

-- EMP004
('EMP004', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-01'), '09:30:00', '17:00:00', 7.50, 'fingerprint', 'present'),
('EMP004', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-02'), NULL, NULL, 0, 'manual', 'absent'),
('EMP004', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-03'), '09:00:00', '17:00:00', 8.00, 'fingerprint', 'present'),
('EMP004', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-04'), '09:15:00', '17:00:00', 7.75, 'fingerprint', 'present'),
('EMP004', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-05'), '09:00:00', '13:00:00', 4.00, 'fingerprint', 'half_day'),

-- EMP005
('EMP005', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-01'), '08:50:00', '17:00:00', 8.17, 'fingerprint', 'present'),
('EMP005', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-02'), '09:00:00', '17:00:00', 8.00, 'fingerprint', 'present'),
('EMP005', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-03'), '09:05:00', '17:00:00', 7.92, 'fingerprint', 'present'),
('EMP005', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-04'), NULL, NULL, 0, 'manual', 'absent'),
('EMP005', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-05'), '09:00:00', '17:00:00', 8.00, 'fingerprint', 'present'),

-- EMP006
('EMP006', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-01'), '09:00:00', '17:00:00', 8.00, 'face', 'present'),
('EMP006', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-02'), '09:10:00', '17:00:00', 7.83, 'face', 'present'),
('EMP006', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-03'), NULL, NULL, 0, 'manual', 'absent'),
('EMP006', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-04'), '09:00:00', '17:00:00', 8.00, 'face', 'present'),
('EMP006', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-05'), '09:00:00', '17:00:00', 8.00, 'face', 'present'),

-- EMP007
('EMP007', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-01'), '08:50:00', '17:30:00', 8.67, 'fingerprint', 'present'),
('EMP007', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-02'), '08:55:00', '17:30:00', 8.58, 'fingerprint', 'present'),
('EMP007', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-03'), '09:00:00', '17:30:00', 8.50, 'fingerprint', 'present'),
('EMP007', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-04'), '08:50:00', '17:30:00', 8.67, 'fingerprint', 'present'),
('EMP007', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-05'), '08:45:00', '17:30:00', 8.75, 'fingerprint', 'present'),

-- EMP008
('EMP008', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-01'), '09:20:00', '17:00:00', 7.67, 'face', 'present'),
('EMP008', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-02'), NULL, NULL, 0, 'manual', 'absent'),
('EMP008', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-03'), '09:00:00', '17:00:00', 8.00, 'face', 'present'),
('EMP008', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-04'), '09:15:00', '17:00:00', 7.75, 'face', 'present'),
('EMP008', CONCAT(@yr,'-',LPAD(@mo,2,'0'),'-05'), '09:00:00', '13:00:00', 4.00, 'face', 'half_day');

USE biometric_attendance;
ALTER TABLE employees ADD COLUMN face_image LONGTEXT DEFAULT NULL;

USE biometric_attendance;
DESCRIBE employees;

INSERT IGNORE INTO employees (emp_id, full_name, department, designation, email, phone, salary, join_date, fingerprint_hash)
VALUES 
('EMP001', 'Dr. Ramesh Kumar', 'Computer Science', 'Professor', 'ramesh@college.edu', '9876543210', 85000.00, '2018-06-01', SHA2('FP_EMP001', 256));
USE biometric_attendance;
ALTER TABLE employees 
MODIFY COLUMN face_encoding TEXT;