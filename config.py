import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ibvap-secure-border-analytics-key-2026')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'ibvap.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Storage paths
    SNAPSHOT_DIR = os.path.join(BASE_DIR, 'static', 'snapshots')
    VIDEO_STORAGE_DIR = os.path.join(BASE_DIR, 'static', 'videos')
    FACE_DB_DIR = os.path.join(BASE_DIR, 'static', 'faces')
    
    # Analytics Thresholds
    YOLO_CONFIDENCE = 0.45
    LOITERING_THRESHOLD_SEC = 5.0  # Seconds inside fence to trigger loitering alert
    SPEED_ANOMALY_THRESHOLD = 30.0 # Pixels per frame threshold for sudden running/movement
    FACE_MATCH_DISTANCE_THRESHOLD = 0.55
    NIGHT_VISION_CONTRAST_CLIP = 3.0
    
    # Video Ingestion Settings
    DEFAULT_STREAM_FPS = 25
    PROCESSING_TARGET_FPS = 15  # Process AI every N frames to ensure low latency on standard hardware
