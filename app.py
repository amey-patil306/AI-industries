# app.py

import os

import cv2
import base64
from flask import Flask, render_template, Response, request, redirect, flash, session
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models.gear_detection import gear_detection
from models.fire_detection import fire_detection
from models.pose import detect_l_pose  # ✅ Changed: import correct function for pose detection

app = Flask(__name__)
app.config['SECRET_KEY'] = 'the random string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.config["SQLALCHEMY_BINDS"] = {
    "cams": "sqlite:///cams.db",
    "alerts": "sqlite:///alerts.db"
}

db = SQLAlchemy(app)
login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    email = db.Column(db.String(100))

class Camera(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) 
    cam_id = db.Column(db.String(100))
    fire_detection = db.Column(db.Boolean, default=False)
    pose_alert = db.Column(db.Boolean, default=False)
    restricted_zone = db.Column(db.Boolean, default=False)
    safety_gear_detection = db.Column(db.Boolean, default=False)
    region = db.Column(db.Boolean, default=False)

class Alert(db.Model):  
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  
    date_time = db.Column(db.DateTime)
    alert_type = db.Column(db.String(50))
    frame_snapshot = db.Column(db.LargeBinary)

# ✅ Model Initializations
fire_det = fire_detection("models/fire.pt", conf=0.60)
gear_det = gear_detection("models/gear.pt")


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login_page')
def login_page():
    return render_template("login.html")

@app.route('/register_page')
def register_page():
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or not password:
            flash('Email or Password Missing!!')
            return redirect('/login')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.password == password:
            login_user(user)
            return redirect('/dashboard')
        else:
            flash('Invalid email or password')
            return redirect('/login')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists.')
            return redirect('/register')

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('User registered successfully! Please log in.')
        return redirect('/login')

    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dash_page():
    cameras = Camera.query.filter_by(user_id=current_user.id).all()
    return render_template('dash.html', cameras=cameras)

@app.route("/manage_camera")
@login_required
def manage_cam_page():
    cameras = Camera.query.filter_by(user_id=current_user.id).all()
    return render_template('manage_cam.html', cameras=cameras)

@app.route("/get_cam_details", methods=['GET', 'POST'])
@login_required
def getting_cam_details():
    if request.method == 'POST':
        camid = request.form['Cam_id']
        fire_bool = "fire" in request.form
        pose_bool = "pose_alert" in request.form
        r_bool = "R_zone" in request.form
        s_gear_bool = "Safety_gear" in request.form

        camera = Camera.query.filter_by(cam_id=camid, user_id=current_user.id).first()

        if camera:
            camera.fire_detection = fire_bool
            camera.pose_alert = pose_bool
            camera.restricted_zone = r_bool
            camera.safety_gear_detection = s_gear_bool
        else:
            camera = Camera(user_id=current_user.id, cam_id=camid, fire_detection=fire_bool,
                            pose_alert=pose_bool, restricted_zone=r_bool,
                            safety_gear_detection=s_gear_bool)

        db.session.add(camera)
        db.session.commit()
    return redirect("/manage_camera")

@app.route('/notifications')
@login_required
def notifications():
    alerts = Alert.query.filter_by(user_id=current_user.id).order_by(Alert.date_time.desc()).all()
    for alert in alerts:
        alert.frame_snapshot = base64.b64encode(alert.frame_snapshot).decode('utf-8')
    return render_template('notifications.html', alerts=alerts)

@app.route('/delete_notification/<int:id>')         
@login_required
def delete_notification(id):
    alert = Alert.query.filter_by(id=id, user_id=current_user.id).first()
    db.session.delete(alert)
    db.session.commit()
    return redirect("/notifications")

@app.route('/delete_camera/<int:id>')               
@login_required
def delete_camera(id):
    camera = Camera.query.filter_by(id=id, user_id=current_user.id).first()
    db.session.delete(camera)
    db.session.commit()
    return redirect("/manage_camera")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/video_feed/<string:cam_id>')
@login_required
def video_feed(cam_id):
    camera = Camera.query.filter_by(cam_id=str(cam_id), user_id=current_user.id).first()
    if camera:
        flag_r_zone = camera.restricted_zone
        flag_pose_alert = camera.pose_alert
        flag_fire = camera.fire_detection
        flag_gear = camera.safety_gear_detection
        region = camera.region
        
        try:
            return Response(process_frames(str(cam_id), region, flag_r_zone, flag_pose_alert,
                                           flag_fire, flag_gear, current_user.id), mimetype='multipart/x-mixed-replace; boundary=frame')
        except:
            return "Something wrong with Cam Details !!"
    else:
        return "Camera details not found."

def add_to_db(results, frame, alert_name, user_id=None):
    if results[0]:
        for box in results[1]:
            x1, y1, x2, y2 = box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

        with app.app_context():
            latest_alert = Alert.query.filter_by(alert_type=alert_name, user_id=user_id).order_by(Alert.date_time.desc()).first()

            if (latest_alert is None) or ((datetime.now() - latest_alert.date_time) > timedelta(minutes=1)):
                new_alert = Alert(date_time=datetime.now(), alert_type=alert_name,
                                  frame_snapshot=cv2.imencode('.jpg', frame)[1].tobytes(),
                                  user_id=user_id)
                db.session.add(new_alert)
                db.session.commit()

def process_frames(camid, region, flag_r_zone=False, flag_pose_alert=False, flag_fire=False, flag_gear=False, user_id=None):
    if len(camid) == 1:
        cap = cv2.VideoCapture(int(camid))
    else:
        address = f"http://{camid}/video"
        print(address)
        cap = cv2.VideoCapture(address)

    if not cap.isOpened():
        raise Exception("Failed to open camera")
    
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    frame_skip = 2
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        if frame_count % frame_skip != 0:
            continue

        frame = cv2.resize(frame, (1000, 580))

        # Fire detection
        results = fire_det.process(img=frame, flag=flag_fire)
        add_to_db(results=results, frame=frame, alert_name="fire_detection", user_id=user_id)

        # Gear detection
        results = gear_det.process(img=frame, flag=flag_gear)
        add_to_db(results=results, frame=frame, alert_name="gear_detection", user_id=user_id)

        # ✅ L-pose Detection
        if flag_pose_alert:
            pose_frame, detected = detect_l_pose(frame.copy())
            if detected:
                with app.app_context():
                    latest_alert = Alert.query.filter_by(alert_type="pose_alert", user_id=user_id).order_by(Alert.date_time.desc()).first()
                    if (latest_alert is None) or ((datetime.now() - latest_alert.date_time) > timedelta(minutes=1)):
                        new_alert = Alert(date_time=datetime.now(), alert_type="pose_alert",
                                          frame_snapshot=cv2.imencode('.jpg', pose_frame)[1].tobytes(),
                                          user_id=user_id)
                        db.session.add(new_alert)
                        db.session.commit()
            frame = pose_frame

        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()

if __name__ == "__main__":
    app.run(debug=True)
