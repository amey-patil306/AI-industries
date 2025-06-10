# app.py

import os
import cv2
import base64
import json
from flask import Flask, render_template, Response, request, redirect, flash, session, jsonify
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# Import detection models
from models.fire_detection import fire_detection
from models.smoke_detection import smoke_detection
from models.gear_detection import gear_detection
from models.enhanced_gear_detection import enhanced_gear_detection
from models.intrusion_detection import intrusion_detection
from models.leakage_detection import leakage_detection
from models.activity_monitoring import activity_monitoring
from models.defect_detection import defect_detection
from models.crowd_detection import crowd_detection
from models.air_quality_detection import air_quality_detection
from models.pose import detect_l_pose

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
    smoke_detection = db.Column(db.Boolean, default=False)
    pose_alert = db.Column(db.Boolean, default=False)
    restricted_zone = db.Column(db.Boolean, default=False)
    safety_gear_detection = db.Column(db.Boolean, default=False)
    enhanced_gear_detection = db.Column(db.Boolean, default=False)
    intrusion_detection = db.Column(db.Boolean, default=False)
    leakage_detection = db.Column(db.Boolean, default=False)
    activity_monitoring = db.Column(db.Boolean, default=False)
    defect_detection = db.Column(db.Boolean, default=False)
    crowd_detection = db.Column(db.Boolean, default=False)
    air_quality_monitoring = db.Column(db.Boolean, default=False)
    region = db.Column(db.Boolean, default=False)

class Alert(db.Model):  
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  
    date_time = db.Column(db.DateTime)
    alert_type = db.Column(db.String(50))
    severity = db.Column(db.String(20), default='medium')
    frame_snapshot = db.Column(db.LargeBinary)
    description = db.Column(db.Text)
    camera_id = db.Column(db.String(100))
    confidence = db.Column(db.Float, default=0.0)

class SystemMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    total_cameras = db.Column(db.Integer, default=0)
    active_alerts = db.Column(db.Integer, default=0)
    system_uptime = db.Column(db.Float, default=0.0)
    detection_accuracy = db.Column(db.Float, default=0.0)

# Initialize detection models
fire_det = fire_detection("models/fire.pt", conf=0.60)
smoke_det = smoke_detection("models/fire.pt", conf=0.70)
gear_det = gear_detection("models/gear.pt")
enhanced_gear_det = enhanced_gear_detection("models/gear.pt", conf=0.75)
intrusion_det = intrusion_detection(conf=0.60)
leakage_det = leakage_detection(conf=0.65)
activity_det = activity_monitoring(conf=0.70)
defect_det = defect_detection(conf=0.80)
crowd_det = crowd_detection(conf=0.60)
air_quality_det = air_quality_detection()

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
    try:
        cameras = Camera.query.filter_by(user_id=current_user.id).all()
        
        # Get dashboard statistics
        total_cameras = len(cameras)
        recent_alerts = Alert.query.filter_by(user_id=current_user.id).filter(
            Alert.date_time >= datetime.now() - timedelta(hours=24)
        ).count()
        
        critical_alerts = Alert.query.filter_by(
            user_id=current_user.id, 
            severity='critical'
        ).filter(
            Alert.date_time >= datetime.now() - timedelta(hours=24)
        ).count()
        
        stats = {
            'total_cameras': total_cameras,
            'recent_alerts': recent_alerts,
            'critical_alerts': critical_alerts,
            'system_status': 'Online' if total_cameras > 0 else 'No Cameras'
        }
        
        return render_template('dashboard.html', cameras=cameras, stats=stats)
    except Exception as e:
        flash(f'Database error: {str(e)}. Please run database migration.')
        return redirect('/login')

@app.route("/manage_camera")
@login_required
def manage_cam_page():
    try:
        cameras = Camera.query.filter_by(user_id=current_user.id).all()
        return render_template('manage_cam.html', cameras=cameras)
    except Exception as e:
        flash(f'Database error: {str(e)}. Please run database migration.')
        return redirect('/dashboard')

@app.route("/get_cam_details", methods=['GET', 'POST'])
@login_required
def getting_cam_details():
    if request.method == 'POST':
        try:
            camid = request.form['Cam_id']
            
            # Get all detection flags
            detection_flags = {
                'fire_detection': "fire" in request.form,
                'smoke_detection': "smoke" in request.form,
                'pose_alert': "pose_alert" in request.form,
                'restricted_zone': "R_zone" in request.form,
                'safety_gear_detection': "Safety_gear" in request.form,
                'enhanced_gear_detection': "Enhanced_gear" in request.form,
                'intrusion_detection': "Intrusion" in request.form,
                'leakage_detection': "Leakage" in request.form,
                'activity_monitoring': "Activity" in request.form,
                'defect_detection': "Defect" in request.form,
                'crowd_detection': "Crowd" in request.form,
                'air_quality_monitoring': "Air_quality" in request.form
            }

            camera = Camera.query.filter_by(cam_id=camid, user_id=current_user.id).first()

            if camera:
                # Update existing camera
                for flag, value in detection_flags.items():
                    setattr(camera, flag, value)
            else:
                # Create new camera
                camera = Camera(
                    user_id=current_user.id, 
                    cam_id=camid,
                    **detection_flags
                )

            db.session.add(camera)
            db.session.commit()
            flash('Camera configuration saved successfully!')
        except Exception as e:
            flash(f'Error saving camera configuration: {str(e)}')
    
    return redirect("/manage_camera")

@app.route('/notifications')
@login_required
def notifications():
    try:
        alerts = Alert.query.filter_by(user_id=current_user.id).order_by(Alert.date_time.desc()).limit(100).all()
        for alert in alerts:
            alert.frame_snapshot = base64.b64encode(alert.frame_snapshot).decode('utf-8')
        return render_template('notifications.html', alerts=alerts)
    except Exception as e:
        flash(f'Database error: {str(e)}. Please run database migration.')
        return redirect('/dashboard')

@app.route('/analytics')
@login_required
def analytics():
    try:
        # Get analytics data
        alerts_by_type = db.session.query(
            Alert.alert_type, 
            db.func.count(Alert.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(Alert.alert_type).all()
        
        alerts_by_severity = db.session.query(
            Alert.severity,
            db.func.count(Alert.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(Alert.severity).all()
        
        # Recent trends (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        daily_alerts = db.session.query(
            db.func.date(Alert.date_time).label('date'),
            db.func.count(Alert.id).label('count')
        ).filter(
            Alert.user_id == current_user.id,
            Alert.date_time >= week_ago
        ).group_by(db.func.date(Alert.date_time)).all()
        
        analytics_data = {
            'alerts_by_type': [{'type': item[0], 'count': item[1]} for item in alerts_by_type],
            'alerts_by_severity': [{'severity': item[0], 'count': item[1]} for item in alerts_by_severity],
            'daily_alerts': [{'date': str(item[0]), 'count': item[1]} for item in daily_alerts]
        }
        
        return render_template('analytics.html', analytics=analytics_data)
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}')
        return redirect('/dashboard')

@app.route('/api/dashboard_stats')
@login_required
def dashboard_stats():
    try:
        cameras = Camera.query.filter_by(user_id=current_user.id).count()
        alerts_today = Alert.query.filter_by(user_id=current_user.id).filter(
            Alert.date_time >= datetime.now().replace(hour=0, minute=0, second=0)
        ).count()
        
        critical_alerts = Alert.query.filter_by(
            user_id=current_user.id,
            severity='critical'
        ).filter(
            Alert.date_time >= datetime.now() - timedelta(hours=24)
        ).count()
        
        return jsonify({
            'total_cameras': cameras,
            'alerts_today': alerts_today,
            'critical_alerts': critical_alerts,
            'system_status': 'Online'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_notification/<int:id>')         
@login_required
def delete_notification(id):
    alert = Alert.query.filter_by(id=id, user_id=current_user.id).first()
    if alert:
        db.session.delete(alert)
        db.session.commit()
        flash('Alert deleted successfully!')
    return redirect("/notifications")

@app.route('/delete_camera/<int:id>')               
@login_required
def delete_camera(id):
    camera = Camera.query.filter_by(id=id, user_id=current_user.id).first()
    if camera:
        db.session.delete(camera)
        db.session.commit()
        flash('Camera deleted successfully!')
    return redirect("/manage_camera")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/video_feed/<string:cam_id>')
@login_required
def video_feed(cam_id):
    try:
        camera = Camera.query.filter_by(cam_id=str(cam_id), user_id=current_user.id).first()
        if camera:
            return Response(
                process_frames(
                    str(cam_id), 
                    camera.region,
                    camera.restricted_zone,
                    camera.pose_alert,
                    camera.fire_detection,
                    camera.smoke_detection,
                    camera.safety_gear_detection,
                    camera.enhanced_gear_detection,
                    camera.intrusion_detection,
                    camera.leakage_detection,
                    camera.activity_monitoring,
                    camera.defect_detection,
                    camera.crowd_detection,
                    camera.air_quality_monitoring,
                    current_user.id
                ), 
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )
        else:
            return "Camera details not found."
    except Exception as e:
        return f"Error with camera: {str(e)}"

def add_to_db(results, frame, alert_name, user_id=None, camera_id=None, severity='medium', description='', confidence=0.0):
    """Enhanced alert logging with additional metadata"""
    if results[0]:  # If detection found
        with app.app_context():
            try:
                latest_alert = Alert.query.filter_by(
                    alert_type=alert_name, 
                    user_id=user_id,
                    camera_id=camera_id
                ).order_by(Alert.date_time.desc()).first()

                # Only add new alert if last one was more than 30 seconds ago
                if (latest_alert is None) or ((datetime.now() - latest_alert.date_time) > timedelta(seconds=30)):
                    new_alert = Alert(
                        date_time=datetime.now(), 
                        alert_type=alert_name,
                        severity=severity,
                        description=description,
                        frame_snapshot=cv2.imencode('.jpg', frame)[1].tobytes(),
                        user_id=user_id,
                        camera_id=camera_id,
                        confidence=confidence
                    )
                    db.session.add(new_alert)
                    db.session.commit()
            except Exception as e:
                print(f"Error adding alert to database: {e}")

def process_frames(camid, region, flag_r_zone=False, flag_pose_alert=False, 
                  flag_fire=False, flag_smoke=False, flag_gear=False, 
                  flag_enhanced_gear=False, flag_intrusion=False, flag_leakage=False,
                  flag_activity=False, flag_defect=False, flag_crowd=False,
                  flag_air_quality=False, user_id=None):
    """Enhanced frame processing with all detection features"""
    
    # Initialize camera
    if len(camid) == 1:
        cap = cv2.VideoCapture(int(camid))
    else:
        address = f"http://{camid}/video"
        cap = cv2.VideoCapture(address)

    if not cap.isOpened():
        raise Exception("Failed to open camera")
    
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    frame_skip = 2
    frame_count = 0

    # Define restricted zones (example coordinates - should be configurable)
    restricted_zones = [[(100, 100), (300, 100), (300, 300), (100, 300)]]

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        if frame_count % frame_skip != 0:
            continue

        frame = cv2.resize(frame, (1000, 580))
        original_frame = frame.copy()

        # Fire Detection
        if flag_fire:
            results = fire_det.process(img=frame, flag=True)
            if results[0]:
                add_to_db(results, frame, "fire_detection", user_id, camid, 'critical', 
                         'Fire detected in monitored area', 0.85)

        # Smoke Detection
        if flag_smoke:
            results = smoke_det.process(img=frame, flag=True)
            if hasattr(results, '__len__') and len(results) >= 3:
                detection_found, boxes, types = results
                if detection_found:
                    description = f"Smoke/Fire detected: {', '.join(types)}"
                    add_to_db((detection_found, boxes), frame, "smoke_detection", user_id, camid, 
                             'high', description, 0.75)

        # Basic Gear Detection
        if flag_gear:
            results = gear_det.process(img=frame, flag=True)
            if results[0]:
                add_to_db(results, frame, "gear_violation", user_id, camid, 'medium', 
                         'Safety gear compliance issue detected', 0.70)

        # Enhanced Gear Detection
        if flag_enhanced_gear:
            results = enhanced_gear_det.process(img=frame, flag=True)
            if results[0]:
                compliance_data = results[2]
                non_compliant = [r for r in compliance_data if not r['compliant']]
                description = f"PPE violations: {len(non_compliant)} workers non-compliant"
                add_to_db(results, frame, "ppe_violation", user_id, camid, 'high', description, 0.80)

        # Intrusion Detection
        if flag_intrusion:
            results = intrusion_det.process(img=frame, flag=True, restricted_zones=restricted_zones)
            if results[0]:
                intrusion_points = results[2]
                description = f"Unauthorized entry detected: {len(intrusion_points)} intrusion(s)"
                add_to_db(results, frame, "intrusion_alert", user_id, camid, 'critical', description, 0.75)

        # Leakage Detection
        if flag_leakage:
            results = leakage_det.process(img=frame, flag=True)
            if results[0]:
                leak_type = results[2] if len(results) > 2 else 'Unknown'
                description = f"Leakage detected: {leak_type}"
                add_to_db(results, frame, "leakage_alert", user_id, camid, 'high', description, 0.70)

        # Activity Monitoring
        if flag_activity:
            results = activity_det.process(img=frame, flag=True)
            if results[0]:
                activities = results[2] if len(results) > 2 else []
                description = f"Activities detected: {', '.join(activities)}"
                add_to_db(results, frame, "activity_alert", user_id, camid, 'low', description, 0.65)

        # Defect Detection
        if flag_defect:
            results = defect_det.process(img=frame, flag=True)
            if results[0]:
                defect_count = len(results[1]) if len(results) > 1 else 1
                description = f"Product defects detected: {defect_count} items"
                add_to_db(results, frame, "defect_alert", user_id, camid, 'medium', description, 0.80)

        # Crowd Detection
        if flag_crowd:
            results = crowd_det.process(img=frame, flag=True)
            if results[0]:
                crowd_density = results[2] if len(results) > 2 else 'High'
                description = f"Crowd density alert: {crowd_density} density detected"
                add_to_db(results, frame, "crowd_alert", user_id, camid, 'medium', description, 0.70)

        # Air Quality Monitoring
        if flag_air_quality:
            results = air_quality_det.process(img=frame, flag=True)
            if results[0]:
                air_quality = results[2] if len(results) > 2 else 'Poor'
                description = f"Air quality alert: {air_quality} air quality detected"
                add_to_db(results, frame, "air_quality_alert", user_id, camid, 'medium', description, 0.60)

        # L-pose Detection (Emergency Alert)
        if flag_pose_alert:
            pose_frame, detected = detect_l_pose(frame.copy())
            if detected:
                with app.app_context():
                    try:
                        latest_alert = Alert.query.filter_by(
                            alert_type="emergency_pose", 
                            user_id=user_id,
                            camera_id=camid
                        ).order_by(Alert.date_time.desc()).first()
                        
                        if (latest_alert is None) or ((datetime.now() - latest_alert.date_time) > timedelta(minutes=1)):
                            new_alert = Alert(
                                date_time=datetime.now(), 
                                alert_type="emergency_pose",
                                severity='critical',
                                description='Emergency L-pose detected - immediate assistance required',
                                frame_snapshot=cv2.imencode('.jpg', pose_frame)[1].tobytes(),
                                user_id=user_id,
                                camera_id=camid,
                                confidence=0.90
                            )
                            db.session.add(new_alert)
                            db.session.commit()
                    except Exception as e:
                        print(f"Error adding pose alert: {e}")
            frame = pose_frame

        # Add timestamp and camera info
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"Camera: {camid} | {timestamp}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Add system status overlay
        status_text = "AI MONITORING ACTIVE"
        cv2.putText(frame, status_text, (10, frame.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Encode and yield frame
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()

if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Database creation error: {e}")
            print("Please run the migration script: python migrate_database.py")
    
    app.run(debug=True)