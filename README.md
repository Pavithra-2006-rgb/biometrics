# 🔐 BiometricMS — Biometric Attendance & Payroll System

A web-based **College Attendance and Payroll Management System** with 
real-time face recognition biometric authentication, built using 
Flask, MySQL, and DeepFace AI.

---

## 🚀 Features

- 👤 **Real-Time Face Recognition** — Uses DeepFace (Facenet512 model) 
  to enroll and verify employee faces via webcam
- 🔵 **Fingerprint Simulation** — Biometric fingerprint enrollment support
- 📅 **Attendance Tracking** — Auto check-in/check-out with timestamps 
  and hours worked calculation
- 💰 **Payroll Generation** — Auto-calculates Basic, HRA, DA, PF, Tax, 
  and Net Salary based on attendance
- 📊 **Dashboard** — Real-time stats with charts for attendance and 
  department strength
- 🔒 **Secure Login** — SHA256 hashed admin authentication
- 📤 **Export CSV** — Download attendance and payroll reports
- 🖨️ **Pay Slips** — Generate and print individual employee pay slips

---

## 🛠️ Tech Stack

| Layer     | Technology                        |
|-----------|-----------------------------------|
| Backend   | Python, Flask, Flask-CORS         |
| Database  | MySQL                             |
| Frontend  | HTML, CSS, JavaScript             |
| AI/ML     | DeepFace, Facenet512, OpenCV      |
| Auth      | SHA256 Hashing                    |

---

## 📁 Project Structure
```
biometric_attendance/
├── backend/
│   └── app.py                  # Flask API + DeepFace logic
├── frontend/
│   ├── templates/
│   │   ├── index.html          # Login page
│   │   ├── dashboard.html      # Stats & charts
│   │   ├── employees.html      # Employee management + face enroll
│   │   ├── attendance.html     # Face check-in / check-out
│   │   └── payroll.html        # Payroll generation & pay slips
│   └── static/
│       ├── css/style.css
│       └── js/app.js
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/biometric-attendance.git
cd biometric-attendance
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup MySQL Database
Run the SQL schema in MySQL Workbench:
```sql
CREATE DATABASE biometric_attendance;
USE biometric_attendance;
-- Run the full schema SQL file
```

Also run this once to add face image column:
```sql
ALTER TABLE employees 
ADD COLUMN IF NOT EXISTS face_image LONGTEXT DEFAULT NULL;
```

### 5. Configure database password
In `backend/app.py`, update:
```python
password=os.getenv('DB_PASSWORD', 'your_mysql_password'),
```

### 6. Run the server
```bash
python backend/app.py
```

Open browser → `http://127.0.0.1:5000`

---

## 🔐 Default Login Credentials

| Role  | Username | Password  |
|-------|----------|-----------|
| Admin | admin    | admin123  |
| HR    | hr       | hr123     |

---

## 📸 How Face Recognition Works

1. **Enroll** — Go to Employees → Click 🔵 → Enroll Face (Live Camera)
   → Align face → Capture → Saved to database

2. **Check In** — Go to Attendance → Select Face Recognition
   → Look at camera → Click Check In
   → DeepFace matches your face against all enrolled employees
   → ✅ Correct face → Checked In
   → ❌ Wrong face → "Face does not match!"

---

## 📦 Dependencies
```
flask
flask-cors
mysql-connector-python
python-dotenv
deepface
tf-keras
opencv-python
numpy
```

---

## 👩‍💻 Developed By

**Pavithra Murthy**  
College Biometric Attendance & Payroll System  
Built with ❤️ using Python, Flask & DeepFace AI
