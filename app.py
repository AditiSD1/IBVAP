import os
import json
from flask import Flask, render_template, request, jsonify, Response, redirect, url_for
from flask_socketio import SocketIO, emit

from config import Config
from database import db, init_db
from models import Camera, VirtualFence, WatchlistFace, WatchlistPlate, Alert, AnalyticsLog
from services.stream_manager import stream_manager
from seed_data import seed_database

app = Flask(__name__)
app.config.from_object(Config)

# Initialize Database & SocketIO
init_db(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent' if 'gevent' in str(type(app)) else 'threading')
stream_manager.init_app(app, socketio)

# Seed database on startup
seed_database(app)

# Start active camera stream workers
stream_manager.start_all_streams()

# --- Page Routes ---

@app.route('/')
def index_page():
    cameras = Camera.query.filter_by(is_active=True).all()
    unack_alerts_count = Alert.query.filter_by(status='UNACKNOWLEDGED').count()
    return render_template('index.html', cameras=cameras, unack_alerts_count=unack_alerts_count)

@app.route('/cameras')
def cameras_page():
    cameras = Camera.query.all()
    return render_template('cameras.html', cameras=cameras)

@app.route('/virtual_fences')
def virtual_fences_page():
    cameras = Camera.query.filter_by(is_active=True).all()
    return render_template('virtual_fences.html', cameras=cameras)

@app.route('/alerts')
def alerts_page():
    alerts = Alert.query.order_by(Alert.timestamp.desc()).all()
    cameras = Camera.query.all()
    return render_template('alerts.html', alerts=alerts, cameras=cameras)

@app.route('/watchlists')
def watchlists_page():
    plates = WatchlistPlate.query.all()
    faces = WatchlistFace.query.all()
    return render_template('watchlists.html', plates=plates, faces=faces)

@app.route('/analytics')
def analytics_page():
    return render_template('analytics.html')


# --- MJPEG Live Video Stream Endpoint ---

@app.route('/api/stream/<int:camera_id>')
def video_stream(camera_id):
    return Response(
        stream_manager.generate_mjpeg_stream(camera_id),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


# --- REST API Endpoints ---

# 1. Camera APIs
@app.route('/api/cameras', methods=['GET'])
def get_cameras():
    cameras = Camera.query.all()
    return jsonify([c.to_dict() for c in cameras])

@app.route('/api/cameras', methods=['POST'])
def add_camera():
    data = request.json
    cam = Camera(
        name=data.get('name', 'New Camera'),
        location=data.get('location', 'Border Post'),
        stream_url=data.get('stream_url', 'SYNTHETIC_INTRUSION'),
        camera_type=data.get('camera_type', 'SYNTHETIC'),
        night_mode=data.get('night_mode', False)
    )
    db.session.add(cam)
    db.session.commit()
    stream_manager.start_stream(cam.id)
    return jsonify(cam.to_dict()), 201

@app.route('/api/cameras/<int:cam_id>/toggle_night', methods=['PUT'])
def toggle_night_mode(cam_id):
    cam = db.session.get(Camera, cam_id)
    if not cam:
        return jsonify({'error': 'Camera not found'}), 404
    cam.night_mode = not cam.night_mode
    db.session.commit()
    return jsonify({'success': True, 'night_mode': cam.night_mode})

# 2. Virtual Fence APIs
@app.route('/api/fences', methods=['GET'])
def get_fences():
    camera_id = request.args.get('camera_id', type=int)
    query = VirtualFence.query
    if camera_id:
        query = query.filter_by(camera_id=camera_id)
    fences = query.all()
    return jsonify([f.to_dict() for f in fences])

@app.route('/api/fences', methods=['POST'])
def save_fence():
    data = request.json
    fence_id = data.get('id')
    
    if fence_id:
        fence = db.session.get(VirtualFence, fence_id)
        if not fence:
            return jsonify({'error': 'Fence not found'}), 404
    else:
        fence = VirtualFence()
        
    fence.camera_id = data['camera_id']
    fence.name = data.get('name', 'Virtual Fence')
    fence.fence_type = data.get('fence_type', 'POLYGON')
    fence.coordinates = json.dumps(data['coordinates'])
    fence.trigger_objects = ",".join(data.get('trigger_objects', ['person', 'car', 'truck']))
    fence.is_active = data.get('is_active', True)
    
    db.session.add(fence)
    db.session.commit()
    return jsonify(fence.to_dict()), 200

@app.route('/api/fences/<int:fence_id>', methods=['DELETE'])
def delete_fence(fence_id):
    fence = db.session.get(VirtualFence, fence_id)
    if not fence:
        return jsonify({'error': 'Fence not found'}), 404
    db.session.delete(fence)
    db.session.commit()
    return jsonify({'success': True})

# 3. Alert APIs
@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    severity = request.args.get('severity')
    status = request.args.get('status')
    camera_id = request.args.get('camera_id', type=int)
    
    query = Alert.query.order_by(Alert.timestamp.desc())
    if severity:
        query = query.filter_by(severity=severity)
    if status:
        query = query.filter_by(status=status)
    if camera_id:
        query = query.filter_by(camera_id=camera_id)
        
    alerts = query.limit(100).all()
    return jsonify([a.to_dict() for a in alerts])

@app.route('/api/alerts/<int:alert_id>/status', methods=['PUT'])
def update_alert_status(alert_id):
    data = request.json
    alert = db.session.get(Alert, alert_id)
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    alert.status = data.get('status', 'ACKNOWLEDGED')
    db.session.commit()
    socketio.emit('alert_status_changed', alert.to_dict())
    return jsonify(alert.to_dict())

# 4. Watchlist APIs
@app.route('/api/watchlists/plates', methods=['POST'])
def add_watchlist_plate():
    data = request.json
    plate = WatchlistPlate(
        plate_number=data['plate_number'].upper().strip(),
        vehicle_info=data.get('vehicle_info', ''),
        threat_level=data.get('threat_level', 'HIGH'),
        description=data.get('description', '')
    )
    db.session.add(plate)
    db.session.commit()
    return jsonify(plate.to_dict()), 201

@app.route('/api/watchlists/plates/<int:plate_id>', methods=['DELETE'])
def delete_watchlist_plate(plate_id):
    plate = db.session.get(WatchlistPlate, plate_id)
    if plate:
        db.session.delete(plate)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/watchlists/faces', methods=['POST'])
def add_watchlist_face():
    data = request.json
    face = WatchlistFace(
        person_name=data['person_name'],
        category=data.get('category', 'SUSPECT'),
        image_path=data.get('image_path', '/static/faces/default.jpg')
    )
    db.session.add(face)
    db.session.commit()
    return jsonify(face.to_dict()), 201

# 5. Analytics Summary API for Command Dashboard
@app.route('/api/analytics/summary', methods=['GET'])
def get_analytics_summary():
    total_cameras = Camera.query.count()
    active_cameras = Camera.query.filter_by(is_active=True).count()
    total_alerts = Alert.query.count()
    unack_alerts = Alert.query.filter_by(status='UNACKNOWLEDGED').count()
    critical_alerts = Alert.query.filter_by(severity='CRITICAL').count()
    
    # Event breakdown
    intrusions = Alert.query.filter_by(event_type='FENCE_INTRUSION').count()
    anpr_matches = Alert.query.filter_by(event_type='ANPR_MATCH').count()
    loiterings = Alert.query.filter_by(event_type='LOITERING').count()
    night_movements = Alert.query.filter_by(event_type='NIGHT_MOVEMENT').count()

    return jsonify({
        'total_cameras': total_cameras,
        'active_cameras': active_cameras,
        'total_alerts': total_alerts,
        'unack_alerts': unack_alerts,
        'critical_alerts': critical_alerts,
        'event_breakdown': {
            'Perimeter Intrusion': intrusions,
            'ANPR Watchlist Match': anpr_matches,
            'Suspicious Loitering': loiterings,
            'Night Movement': night_movements
        }
    })


# WebSocket Connections
@socketio.on('connect')
def handle_connect():
    print("[WEBSOCKET] Client connected to IBVAP C2 Command Center")
    emit('system_status', {'message': 'Connected to IBVAP AI Video Analytics Core'})

if __name__ == '__main__':
    print("[SERVER] Launching IBVAP Command & Control Center on http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
