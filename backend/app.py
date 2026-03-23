from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import mysql.connector
import os
import hashlib
import base64
import json
from datetime import datetime, date, timedelta
import calendar
from dotenv import load_dotenv
import numpy as np
import tempfile

# ── DeepFace safe import ───────────────────────────────────────
try:
    from deepface import DeepFace
    DEEPFACE_OK = True
    print("✅ DeepFace loaded!")
except ImportError:
    DEEPFACE_OK = False
    print("⚠️  DeepFace not found. Run: pip install deepface tf-keras opencv-python")

load_dotenv()

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
CORS(app)

# ─── DB Config ────────────────────────────────────────────────────────────────
def get_db():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'pavi@2006'),
        database=os.getenv('DB_NAME', 'biometric_attendance'),
        port=int(os.getenv('DB_PORT', 3306))
    )

# ─── Routes: Pages ────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/attendance')
def attendance_page():
    return render_template('attendance.html')

@app.route('/payroll')
def payroll_page():
    return render_template('payroll.html')

@app.route('/employees')
def employees_page():
    return render_template('employees.html')

# ─── API: Auth ─────────────────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = hashlib.sha256(data.get('password', '').encode()).hexdigest()
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM admin_users WHERE username=%s AND password=%s", (username, password))
    user = cur.fetchone()
    db.close()
    if user:
        return jsonify({'success': True, 'role': user['role'], 'name': user['full_name']})
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

# ─── API: Employees ────────────────────────────────────────────────────────────
@app.route('/api/employees', methods=['GET'])
def get_employees():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM employees ORDER BY emp_id")
    employees = cur.fetchall()
    db.close()
    return jsonify(employees)

@app.route('/api/employees', methods=['POST'])
def add_employee():
    data = request.json
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO employees (emp_id, full_name, department, designation, email, phone, 
                               salary, join_date, fingerprint_hash, face_encoding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (data['emp_id'], data['full_name'], data['department'], data['designation'],
          data['email'], data['phone'], data['salary'], data['join_date'],
          data.get('fingerprint_hash', ''), data.get('face_encoding', '')))
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': 'Employee added successfully'})

@app.route('/api/employees/<emp_id>', methods=['PUT'])
def update_employee(emp_id):
    data = request.json
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        UPDATE employees SET full_name=%s, department=%s, designation=%s, 
        email=%s, phone=%s, salary=%s WHERE emp_id=%s
    """, (data['full_name'], data['department'], data['designation'],
          data['email'], data['phone'], data['salary'], emp_id))
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': 'Employee updated'})

@app.route('/api/employees/<emp_id>', methods=['DELETE'])
def delete_employee(emp_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM employees WHERE emp_id=%s", (emp_id,))
    db.commit()
    db.close()
    return jsonify({'success': True})

# ─── API: Biometric Simulation ─────────────────────────────────────────────────
@app.route('/api/biometric/fingerprint', methods=['POST'])
def fingerprint_auth():
    """Simulate fingerprint scan - in prod, this receives actual scanner data"""
    data = request.json
    fingerprint_data = data.get('fingerprint_data', '')
    # Simulate matching by hashing the received data
    fp_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM employees WHERE fingerprint_hash=%s", (fp_hash,))
    employee = cur.fetchone()
    db.close()
    if employee:
        return jsonify({'success': True, 'employee': employee})
    return jsonify({'success': False, 'message': 'Fingerprint not recognized'}), 404

@app.route('/api/biometric/face', methods=['POST'])
def face_auth():
    """Simulate face recognition - receives base64 image"""
    data = request.json
    face_data = data.get('face_encoding', '')
    db = get_db()
    cur = db.cursor(dictionary=True)
    # In production: use DeepFace or face_recognition library to compare embeddings
    # Here we simulate by direct match on stored encoding
    cur.execute("SELECT * FROM employees WHERE face_encoding=%s", (face_data,))
    employee = cur.fetchone()
    db.close()
    if employee:
        return jsonify({'success': True, 'employee': employee})
    return jsonify({'success': False, 'message': 'Face not recognized'}), 404

# ─── API: Enroll Fingerprint (simulation) ─────────────────────────────────────
@app.route('/api/employees/<emp_id>/enroll', methods=['POST'])
def enroll_biometric(emp_id):
    data = request.json
    biometric_type = data.get('type')
    biometric_data = data.get('data', '')
    bio_hash = hashlib.sha256(biometric_data.encode()).hexdigest()
    db = get_db()
    cur = db.cursor()
    if biometric_type == 'fingerprint':
        cur.execute("UPDATE employees SET fingerprint_hash=%s WHERE emp_id=%s", (bio_hash, emp_id))
    else:
        cur.execute("UPDATE employees SET face_encoding=%s WHERE emp_id=%s", (bio_hash, emp_id))
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': f'{biometric_type} enrolled successfully'})


# ─── API: Enroll Real Face via Webcam ─────────────────────────────────────────
@app.route('/api/employees/<emp_id>/enroll-face', methods=['POST'])
def enroll_face(emp_id):
    """
    Receives webcam image (base64), detects face, saves to DB.
    Works for ALL employees — existing and newly added.
    """
    try:
        data       = request.json
        image_data = data.get('image', '')
        if not image_data:
            return jsonify({'success': False, 'message': 'No image received!'})

        img_bytes = base64.b64decode(image_data.split(',')[1])

        # Write to temp file for DeepFace
        tmp = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        tmp.write(img_bytes)
        tmp.close()

        if DEEPFACE_OK:
            try:
                faces = DeepFace.extract_faces(
                    img_path=tmp.name,
                    enforce_detection=True,
                    detector_backend='opencv'
                )
                os.unlink(tmp.name)
                if not faces:
                    return jsonify({'success': False, 'message': '❌ No face detected! Look directly at the camera.'})
            except Exception:
                os.unlink(tmp.name)
                return jsonify({'success': False, 'message': '❌ No face detected! Look directly at camera in good light.'})
        else:
            os.unlink(tmp.name)

        # Save face image to database
        face_b64 = base64.b64encode(img_bytes).decode('utf-8')
        db  = get_db()
        cur = db.cursor()
        cur.execute(
            "UPDATE employees SET face_image=%s, face_encoding='enrolled' WHERE emp_id=%s",
            (face_b64, emp_id)
        )
        db.commit()
        db.close()
        return jsonify({'success': True, 'message': '✅ Face enrolled successfully!'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

# At top (outside routes)
model = None
if DEEPFACE_OK:
    model = DeepFace.build_model("SFace")
# ─── API: Face Check-In / Check-Out (REAL matching) ───────────────────────────
@app.route('/api/attendance/face-checkin', methods=['POST'])
def face_checkin():
    """
    Captures webcam image → compares with ALL enrolled employees via DeepFace.
    Match   → check in / out that employee.
    No match → "Face does not match!" message.
    """
    try:
        if not DEEPFACE_OK:
            return jsonify({'success': False,
                            'message': '❌ DeepFace not installed! Run: pip install deepface tf-keras opencv-python'})

        data       = request.json
        image_data = data.get('image', '')
        action     = data.get('action', 'checkin')
        today      = date.today()
        now        = datetime.now()

        if not image_data:
            return jsonify({'success': False, 'message': 'No image received!'})

        # Save captured face to temp
        img_bytes = base64.b64decode(image_data.split(',')[1])
        cap_tmp   = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        cap_tmp.write(img_bytes); cap_tmp.close()
        captured_path = cap_tmp.name

        # Load all enrolled employees
        db  = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT emp_id, full_name, face_image
            FROM employees
            WHERE face_image IS NOT NULL AND face_encoding = 'enrolled'
        """)
        enrolled = cur.fetchall()

        if not enrolled:
            db.close()
            os.unlink(captured_path)
            return jsonify({'success': False,
                            'message': '❌ No employees enrolled yet! Go to Employees → Enroll Face first.'})

        # Compare captured face against every enrolled face
        matched   = None
        enr_path  = None
        for emp in enrolled:
            try:
                enr_bytes = base64.b64decode(emp['face_image'])
                enr_tmp   = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                enr_tmp.write(enr_bytes); enr_tmp.close()
                enr_path  = enr_tmp.name
                
                

                result = DeepFace.verify(
                    img1_path=captured_path,
                    img2_path=enr_path,
                    model_name='SFace',
                    enforce_detection=False,
                    distance_metric='cosine'
                )
                os.unlink(enr_path)

                if result['verified']:
                    matched = emp
                    print(f"✅ Matched: {emp['full_name']} dist={result['distance']:.3f}")
                    break
                else:
                    print(f"❌ No match: {emp['full_name']} dist={result['distance']:.3f}")

            except Exception as ex:
                print(f"Compare error {emp['emp_id']}: {ex}")
                if enr_path and os.path.exists(enr_path):
                    os.unlink(enr_path)
                continue

        os.unlink(captured_path)

        if not matched:
            db.close()
            return jsonify({'success': False,
                            'message': '❌ Face does not match! This person is not enrolled or face is unclear.'})

        emp_id   = matched['emp_id']
        emp_name = matched['full_name']

        # ── CHECK IN ──────────────────────────────────────────
        if action == 'checkin':
            cur.execute("SELECT * FROM attendance WHERE emp_id=%s AND att_date=%s", (emp_id, today))
            if cur.fetchone():
                db.close()
                return jsonify({'success': False,
                                'message': f'⚠️ {emp_name} already checked in today!',
                                'employee': emp_name})
            cur2 = db.cursor()
            cur2.execute(
                "INSERT INTO attendance (emp_id, att_date, check_in, method, status) VALUES (%s,%s,%s,%s,%s)",
                (emp_id, today, now.time(), 'face', 'present')
            )
            db.commit(); db.close()
            return jsonify({'success': True,
                            'message': f'✅ Checked in at {now.strftime("%H:%M:%S")}',
                            'employee': emp_name, 'emp_id': emp_id})

        # ── CHECK OUT ─────────────────────────────────────────
        else:
            cur.execute("SELECT * FROM attendance WHERE emp_id=%s AND att_date=%s", (emp_id, today))
            record = cur.fetchone()
            if not record:
                db.close()
                return jsonify({'success': False,
                                'message': f'❌ {emp_name} has not checked in today!',
                                'employee': emp_name})
            if record['check_out']:
                db.close()
                return jsonify({'success': False,
                                'message': f'⚠️ {emp_name} already checked out today!',
                                'employee': emp_name})

            def to_sec(t):
                if hasattr(t, 'total_seconds'): return int(t.total_seconds())
                return t.hour*3600 + t.minute*60 + t.second

            hours = round(max(0, (now.hour*3600 + now.minute*60 + now.second) - to_sec(record['check_in'])) / 3600, 2)
            cur2  = db.cursor()
            cur2.execute(
                "UPDATE attendance SET check_out=%s, hours_worked=%s WHERE emp_id=%s AND att_date=%s",
                (now.time(), hours, emp_id, today)
            )
            db.commit(); db.close()
            return jsonify({'success': True,
                            'message': f'✅ Checked out at {now.strftime("%H:%M:%S")}',
                            'employee': emp_name, 'emp_id': emp_id, 'hours_worked': hours})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

# ─── API: Attendance ───────────────────────────────────────────────────────────
@app.route('/api/attendance/checkin', methods=['POST'])
def check_in():
    try:
        data = request.json
        emp_id = data.get('emp_id')
        method = data.get('method', 'manual')
        today = date.today()
        now = datetime.now()

        db = get_db()
        cur = db.cursor(dictionary=True)

        # ── Check if employee exists ────────────────────────────
        cur.execute("SELECT * FROM employees WHERE emp_id=%s", (emp_id,))
        employee = cur.fetchone()

        if not employee:
            db.close()
            return jsonify({
                'success': False,
                'message': 'Employee not found!'
            })

        # ── Check Biometric Enrolled ────────────────────────────
        if method == 'fingerprint':
            if not employee['fingerprint_hash']:
                db.close()
                return jsonify({
                    'success': False,
                    'message': f'❌ Biometric not enrolled! Please enroll fingerprint for {employee["full_name"]} first.'
                })

        if method == 'face':
            if not employee['face_encoding']:
                db.close()
                return jsonify({
                    'success': False,
                    'message': f'❌ Biometric not enrolled! Please enroll Face ID for {employee["full_name"]} first.'
                })

        # ── Check already checked in ────────────────────────────
        cur.execute("""
            SELECT * FROM attendance 
            WHERE emp_id=%s AND att_date=%s
        """, (emp_id, today))
        existing = cur.fetchone()

        if existing:
            db.close()
            return jsonify({
                'success': False,
                'message': f'Already checked in today at {str(existing["check_in"])}'
            })

        # ── Mark Present ────────────────────────────────────────
        cur2 = db.cursor()
        cur2.execute("""
            INSERT INTO attendance (emp_id, att_date, check_in, method, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (emp_id, today, now.time(), method, 'present'))
        db.commit()
        db.close()

        return jsonify({
            'success': True,
            'message': f'Checked in at {now.strftime("%H:%M:%S")}',
            'time': now.strftime("%H:%M:%S")
        })

    except Exception as ex:
        return jsonify({
            'success': False,
            'message': f'Error: {str(ex)}'
        })

@app.route('/api/attendance/checkout', methods=['POST'])
def check_out():
    try:
        data = request.json
        emp_id = data.get('emp_id')
        method = data.get('method', 'manual')
        today = date.today()
        now = datetime.now()

        db = get_db()
        cur = db.cursor(dictionary=True)

        # ── Check if employee exists ────────────────────────────
        cur.execute("SELECT * FROM employees WHERE emp_id=%s", (emp_id,))
        employee = cur.fetchone()

        if not employee:
            db.close()
            return jsonify({
                'success': False,
                'message': 'Employee not found!'
            })

        # ── Check Biometric Enrolled ────────────────────────────
        if method == 'fingerprint':
            if not employee['fingerprint_hash']:
                db.close()
                return jsonify({
                    'success': False,
                    'message': f'❌ Biometric not enrolled! Please enroll fingerprint for {employee["full_name"]} first.'
                })

        if method == 'face':
            if not employee['face_encoding']:
                db.close()
                return jsonify({
                    'success': False,
                    'message': f'❌ Biometric not enrolled! Please enroll Face ID for {employee["full_name"]} first.'
                })

        # ── Find today's check-in record ────────────────────────
        cur.execute("""
            SELECT * FROM attendance 
            WHERE emp_id=%s AND att_date=%s
        """, (emp_id, today))
        record = cur.fetchone()

        # ── No check-in found ───────────────────────────────────
        if not record:
            db.close()
            return jsonify({
                'success': False,
                'message': 'No check-in found for today. Please check in first!'
            })

        # ── Already checked out ─────────────────────────────────
        if record['check_out']:
            db.close()
            return jsonify({
                'success': False,
                'message': 'Already checked out today!'
            })

        # ── Fix timedelta issue from MySQL ──────────────────────
        def to_seconds(t):
            if hasattr(t, 'total_seconds'):
                return int(t.total_seconds())
            elif hasattr(t, 'hour'):
                return t.hour * 3600 + t.minute * 60 + t.second
            else:
                return 0

        check_in_seconds = to_seconds(record['check_in'])
        now_seconds = now.hour * 3600 + now.minute * 60 + now.second

        diff_seconds = now_seconds - check_in_seconds
        if diff_seconds < 0:
            diff_seconds = 0

        hours = round(diff_seconds / 3600, 2)

        # ── Update checkout record ──────────────────────────────
        cur2 = db.cursor()
        cur2.execute("""
            UPDATE attendance 
            SET check_out=%s, hours_worked=%s 
            WHERE emp_id=%s AND att_date=%s
        """, (now.time(), hours, emp_id, today))
        db.commit()
        db.close()

        return jsonify({
            'success': True,
            'message': f'Checked out at {now.strftime("%H:%M:%S")}',
            'hours_worked': hours
        })

    except Exception as ex:
        return jsonify({
            'success': False,
            'message': f'Error: {str(ex)}'
        })

@app.route('/api/attendance/mark-absent', methods=['POST'])
def mark_absent():
    try:
        today = date.today()
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT emp_id FROM employees")
        all_emps = [r['emp_id'] for r in cur.fetchall()]
        cur.execute("SELECT emp_id FROM attendance WHERE att_date=%s", (today,))
        present  = [r['emp_id'] for r in cur.fetchall()]
        absent   = [e for e in all_emps if e not in present]
        cur2 = db.cursor()
        for eid in absent:
            cur2.execute(
                "INSERT IGNORE INTO attendance (emp_id, att_date, method, status) VALUES (%s,%s,%s,%s)",
                (eid, today, 'manual', 'absent')
            )
        db.commit()
        db.close()
        return jsonify({'success': True, 'message': f'Marked {len(absent)} absent',
                        'present_count': len(present), 'absent_count': len(absent)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    month = request.args.get('month', date.today().month)
    year = request.args.get('year', date.today().year)
    emp_id = request.args.get('emp_id', None)
    db = get_db()
    cur = db.cursor(dictionary=True)
    if emp_id:
        cur.execute("""
            SELECT a.*, e.full_name, e.department FROM attendance a
            JOIN employees e ON a.emp_id = e.emp_id
            WHERE a.emp_id=%s AND MONTH(a.att_date)=%s AND YEAR(a.att_date)=%s
            ORDER BY a.att_date DESC
        """, (emp_id, month, year))
    else:
        cur.execute("""
            SELECT a.*, e.full_name, e.department FROM attendance a
            JOIN employees e ON a.emp_id = e.emp_id
            WHERE MONTH(a.att_date)=%s AND YEAR(a.att_date)=%s
            ORDER BY a.att_date DESC, e.full_name
        """, (month, year))
    records = cur.fetchall()
    # Convert time objects to string
    for r in records:
        r['att_date'] = str(r['att_date'])
        r['check_in'] = str(r['check_in']) if r['check_in'] else None
        r['check_out'] = str(r['check_out']) if r['check_out'] else None
    db.close()
    return jsonify(records)

@app.route('/api/attendance/today', methods=['GET'])
def today_attendance():
    today = date.today()
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT a.*, e.full_name, e.department FROM attendance a
        JOIN employees e ON a.emp_id = e.emp_id
        WHERE a.att_date=%s ORDER BY a.check_in
    """, (today,))
    records = cur.fetchall()
    for r in records:
        r['att_date'] = str(r['att_date'])
        r['check_in'] = str(r['check_in']) if r['check_in'] else None
        r['check_out'] = str(r['check_out']) if r['check_out'] else None
    db.close()
    return jsonify(records)

@app.route('/api/attendance/stats', methods=['GET'])
def attendance_stats():
    month = int(request.args.get('month', date.today().month))
    year = int(request.args.get('year', date.today().year))
    working_days = sum(1 for day in range(1, calendar.monthrange(year, month)[1]+1)
                       if date(year, month, day).weekday() < 5)
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT e.emp_id, e.full_name, e.department,
               COUNT(CASE WHEN a.status='present' THEN 1 END) as present_days,
               COUNT(CASE WHEN a.status='absent' THEN 1 END) as absent_days,
               COUNT(CASE WHEN a.status='half_day' THEN 1 END) as half_days,
               ROUND(SUM(a.hours_worked),2) as total_hours
        FROM employees e
        LEFT JOIN attendance a ON e.emp_id=a.emp_id 
            AND MONTH(a.att_date)=%s AND YEAR(a.att_date)=%s
        GROUP BY e.emp_id, e.full_name, e.department
    """, (month, year))
    stats = cur.fetchall()
    for s in stats:
        s['working_days'] = working_days
    # Only count days UP TO TODAY, not entire month
    today = date.today()
    if today.month == month and today.year == year:
        days_passed = sum(1 for day in range(1, today.day + 1)
                         if date(year, month, day).weekday() < 5)
    else:
        days_passed = working_days
    
    present = s['present_days'] or 0
    half = s['half_days'] or 0
    today_date = date.today()
    for s in stats:
        s['working_days'] = working_days
    if today_date.month == month and today_date.year == year:
        days_passed = sum(1 for day in range(1, today_date.day + 1)
                         if date(year, month, day).weekday() < 5)
    else:
        days_passed = working_days
    present = s['present_days'] or 0
    half = s['half_days'] or 0
    s['absent_days'] = max(0, days_passed - present - half)
    s['working_days'] = working_days
    s['days_passed'] = days_passed
    db.close()
    return jsonify(stats)

# ─── API: Payroll ──────────────────────────────────────────────────────────────
@app.route('/api/payroll/generate', methods=['POST'])
def generate_payroll():
    data = request.json
    month = data.get('month', date.today().month)
    year = data.get('year', date.today().year)
    working_days = sum(1 for day in range(1, calendar.monthrange(year, month)[1]+1)
                       if date(year, month, day).weekday() < 5)
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT e.emp_id, e.full_name, e.department, e.designation, e.salary,
               COUNT(CASE WHEN a.status='present' THEN 1 END) as present_days,
               COUNT(CASE WHEN a.status='half_day' THEN 1 END) as half_days
        FROM employees e
        LEFT JOIN attendance a ON e.emp_id=a.emp_id 
            AND MONTH(a.att_date)=%s AND YEAR(a.att_date)=%s
        GROUP BY e.emp_id, e.full_name, e.department, e.designation, e.salary
    """, (month, year))
    employees = cur.fetchall()
    cur2 = db.cursor()
    for emp in employees:
        present = emp['present_days'] or 0
        half = emp['half_days'] or 0
        effective_days = present + (half * 0.5)
        per_day = float(emp['salary']) / working_days if working_days else 0
        basic = round(per_day * effective_days, 2)
        hra = round(basic * 0.20, 2)
        da = round(basic * 0.10, 2)
        pf = round(basic * 0.12, 2)
        tax = round(basic * 0.05, 2)
        gross = round(basic + hra + da, 2)
        deductions = round(pf + tax, 2)
        net = round(gross - deductions, 2)
        absent_days = working_days - present - half
        # Check if payroll already exists
        cur2.execute("SELECT id FROM payroll WHERE emp_id=%s AND month=%s AND year=%s",
                     (emp['emp_id'], month, year))
        existing = cur2.fetchone()
        if existing:
            cur2.execute("""
                UPDATE payroll SET present_days=%s, absent_days=%s, half_days=%s,
                basic_salary=%s, hra=%s, da=%s, pf=%s, tax=%s,
                gross_salary=%s, deductions=%s, net_salary=%s WHERE id=%s
            """, (present, absent_days, half, basic, hra, da, pf, tax, gross, deductions, net, existing[0]))
        else:
            cur2.execute("""
                INSERT INTO payroll (emp_id, month, year, present_days, absent_days, half_days,
                    basic_salary, hra, da, pf, tax, gross_salary, deductions, net_salary)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (emp['emp_id'], month, year, present, absent_days, half,
                  basic, hra, da, pf, tax, gross, deductions, net))
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': f'Payroll generated for {month}/{year}'})

@app.route('/api/payroll', methods=['GET'])
def get_payroll():
    month = request.args.get('month', date.today().month)
    year = request.args.get('year', date.today().year)
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT p.*, e.full_name, e.department, e.designation FROM payroll p
        JOIN employees e ON p.emp_id = e.emp_id
        WHERE p.month=%s AND p.year=%s ORDER BY e.full_name
    """, (month, year))
    payroll = cur.fetchall()
    db.close()
    return jsonify(payroll)

@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    db = get_db()
    cur = db.cursor(dictionary=True)
    today = date.today()
    cur.execute("SELECT COUNT(*) as total FROM employees")
    total_emp = cur.fetchone()['total']
    cur.execute("SELECT COUNT(DISTINCT emp_id) as present FROM attendance WHERE att_date=%s", (today,))
    present_today = cur.fetchone()['present']
    cur.execute("""
        SELECT SUM(net_salary) as total_payroll FROM payroll 
        WHERE month=%s AND year=%s
    """, (today.month, today.year))
    row = cur.fetchone()
    total_payroll = float(row['total_payroll']) if row['total_payroll'] else 0
    cur.execute("SELECT department, COUNT(*) as count FROM employees GROUP BY department")
    dept_stats = cur.fetchall()
    db.close()
    return jsonify({
        'total_employees': total_emp,
        'present_today': present_today,
        'absent_today': total_emp - present_today,
        'total_payroll': total_payroll,
        'dept_stats': dept_stats
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
