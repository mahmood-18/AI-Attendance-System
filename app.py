from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from deepface import DeepFace
import cv2
import numpy as np
import os
from datetime import datetime, date
from io import BytesIO
import pdfkit  # for PDF generation

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-super-secret-key-change-this-please-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ── Models ────────────────────────────────────────────────────────────────
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='student')  # student, teacher, admin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_in = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='present')
    confidence = db.Column(db.Float, default=0.0)
    user = db.relationship('User', backref='attendances')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ── Face Recognition Setup ────────────────────────────────────────────────
KNOWN_FACES_DIR = "known_faces"
RECOGNITION_THRESHOLD = 0.42  # cosine distance - adjust based on testing

def initialize_known_faces():
    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
    count = sum(1 for f in os.listdir(KNOWN_FACES_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png')))
    print(f"[INFO] {count} known face images found in '{KNOWN_FACES_DIR}'")
    if count == 0:
        print("[WARNING] No images in known_faces/ → everyone will be Unknown")

initialize_known_faces()

def gen_frames():
    cap = cv2.VideoCapture(0)  # change to 1 or 2 if default webcam fails
    if not cap.isOpened():
        print("[ERROR] Cannot open webcam")
        black = np.zeros((480, 640, 3), np.uint8)
        ret, buffer = cv2.imencode('.jpg', black)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        return

    while True:
        success, frame = cap.read()
        if not success:
            break

        display_frame = frame.copy()
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

        name = "Unknown"
        confidence_text = ""
        color = (0, 0, 255)  # BGR red

        try:
            results = DeepFace.find(
                img_path=small_frame,
                db_path=KNOWN_FACES_DIR,
                model_name="ArcFace",
                detector_backend="opencv",
                enforce_detection=False,
                distance_metric="cosine",
                silent=True
            )

            if results and len(results) > 0 and len(results[0]) > 0:
                best = results[0].iloc[0]
                distance = best["distance"]
                if distance < RECOGNITION_THRESHOLD:
                    name = os.path.splitext(os.path.basename(best["identity"]))[0]
                    confidence = max(0, min(100, round((1 - distance) * 100, 1)))
                    confidence_text = f"{confidence}%"
                    color = (0, 255, 0)  # green

        except Exception as e:
            print(f"[DeepFace error in frame] {e}")

        # Draw overlay on frame
        cv2.rectangle(display_frame, (20, 20), (340, 100), color, 2)
        cv2.putText(display_frame, name, (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
        if confidence_text:
            cv2.putText(display_frame, confidence_text, (30, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        ret, buffer = cv2.imencode('.jpg', display_frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    cap.release()

# ── Routes ────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name', '')

        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('login'))

        user = User(username=username, email=email, full_name=full_name)
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Try again.', 'danger')
            print(e)
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    today_att = Attendance.query.filter_by(user_id=current_user.id, date=date.today()).first()
    total_days = Attendance.query.filter_by(user_id=current_user.id).count()
    present_days = Attendance.query.filter_by(user_id=current_user.id, status='present').count()
    percentage = round((present_days / total_days * 100), 1) if total_days > 0 else 0.0

    return render_template('dashboard.html',
                           today_attendance=today_att,
                           attendance_percentage=percentage)

@app.route('/attendance')
@login_required
def attendance():
    return render_template('attendance.html')

@app.route('/video_feed')
@login_required
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/mark_attendance', methods=['POST'])
@login_required
def mark_attendance():
    today = date.today()
    if Attendance.query.filter_by(user_id=current_user.id, date=today).first():
        return jsonify({'success': False, 'message': 'Already marked today'})

    # Placeholder confidence (in real system: verify face matches user)
    confidence = 0.92

    att = Attendance(
        user_id=current_user.id,
        date=today,
        time_in=datetime.now(),
        confidence=confidence
    )
    db.session.add(att)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Attendance marked at {datetime.now().strftime("%I:%M %p")}',
        'confidence': confidence
    })

@app.route('/reports')
@login_required
def reports():
    attendances = Attendance.query.filter_by(user_id=current_user.id)\
                                  .order_by(Attendance.date.desc()).all()

    dates = [att.date.strftime('%Y-%m-%d') for att in attendances]
    present_flags = [1 if att.status == 'present' else 0 for att in attendances]

    return render_template('reports.html',
                           attendances=attendances,
                           dates=dates,
                           present_flags=present_flags)

@app.route('/download_report')
@login_required
def download_report():
    attendances = Attendance.query.filter_by(user_id=current_user.id)\
                                  .order_by(Attendance.date.desc()).all()

    html_content = render_template('report_pdf.html',
                                   attendances=attendances,
                                   user=current_user,
                                   today=date.today())

    # Generate PDF using pdfkit (wkhtmltopdf must be installed)
    try:
        pdf_bytes = pdfkit.from_string(html_content, False)
    except Exception as e:
        flash(f"PDF generation failed: {str(e)}", 'danger')
        return redirect(url_for('reports'))

    pdf_io = BytesIO(pdf_bytes)
    pdf_io.seek(0)

    filename = f"attendance_report_{current_user.username}_{date.today()}.pdf"

    return send_file(
        pdf_io,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)