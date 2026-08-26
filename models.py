from datetime import datetime
import json
from database import db

class Camera(db.Model):
    __tablename__ = 'cameras'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False) # e.g., BOP Alpha, Checkpost Bravo, Sector 4 Fence
    stream_url = db.Column(db.String(255), nullable=False) # RTSP URL, MP4 path, webcam index (0), or synth keyword
    camera_type = db.Column(db.String(50), default='IP_RTSP') # IP_RTSP, USB_WEBCAM, FILE, SYNTHETIC
    is_active = db.Column(db.Boolean, default=True)
    night_mode = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    fences = db.relationship('VirtualFence', backref='camera', lazy=True, cascade="all, delete-orphan")
    alerts = db.relationship('Alert', backref='camera', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'stream_url': self.stream_url,
            'camera_type': self.camera_type,
            'is_active': self.is_active,
            'night_mode': self.night_mode,
            'fence_count': len(self.fences),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class VirtualFence(db.Model):
    __tablename__ = 'virtual_fences'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    fence_type = db.Column(db.String(50), default='POLYGON') # POLYGON, TRIPWIRE
    coordinates = db.Column(db.Text, nullable=False) # JSON array of [x, y] points normalized (0.0 to 1.0)
    trigger_objects = db.Column(db.String(100), default='person,car,truck') # Comma separated
    is_active = db.Column(db.Boolean, default=True)
    
    def get_coordinates_list(self):
        try:
            return json.loads(self.coordinates)
        except Exception:
            return []

    def to_dict(self):
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'name': self.name,
            'fence_type': self.fence_type,
            'coordinates': self.get_coordinates_list(),
            'trigger_objects': self.trigger_objects.split(','),
            'is_active': self.is_active
        }

class WatchlistFace(db.Model):
    __tablename__ = 'watchlist_faces'
    
    id = db.Column(db.Integer, primary_key=True)
    person_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), default='SUSPECT') # SUSPECT, INFILTRATOR, AUTHORIZED, VIP
    image_path = db.Column(db.String(255), nullable=False)
    embedding_json = db.Column(db.Text, nullable=True) # Feature vector JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'person_name': self.person_name,
            'category': self.category,
            'image_path': self.image_path,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class WatchlistPlate(db.Model):
    __tablename__ = 'watchlist_plates'
    
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(50), nullable=False, unique=True)
    vehicle_info = db.Column(db.String(100), nullable=True)
    threat_level = db.Column(db.String(50), default='HIGH') # CRITICAL, HIGH, MEDIUM
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'plate_number': self.plate_number,
            'vehicle_info': self.vehicle_info,
            'threat_level': self.threat_level,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False) # FENCE_INTRUSION, ANPR_MATCH, FRS_MATCH, LOITERING, NIGHT_MOVEMENT, SPEED_ANOMALY
    severity = db.Column(db.String(20), default='HIGH') # CRITICAL, HIGH, MEDIUM, LOW
    description = db.Column(db.Text, nullable=False)
    snapshot_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(30), default='UNACKNOWLEDGED') # UNACKNOWLEDGED, ACKNOWLEDGED, RESOLVED
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'camera_name': self.camera.name if self.camera else f"Camera #{self.camera_id}",
            'location': self.camera.location if self.camera else "Unknown Location",
            'event_type': self.event_type,
            'severity': self.severity,
            'description': self.description,
            'snapshot_path': self.snapshot_path,
            'status': self.status,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

class AnalyticsLog(db.Model):
    __tablename__ = 'analytics_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False)
    date_hour = db.Column(db.String(20), nullable=False) # e.g. '2026-08-24 08:00'
    human_count = db.Column(db.Integer, default=0)
    vehicle_count = db.Column(db.Integer, default=0)
    intrusion_count = db.Column(db.Integer, default=0)
    anpr_count = db.Column(db.Integer, default=0)
    frs_count = db.Column(db.Integer, default=0)
    night_movement_count = db.Column(db.Integer, default=0)
