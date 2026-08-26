import os
import json
from datetime import datetime
from config import Config
from database import db
from models import Camera, VirtualFence, WatchlistFace, WatchlistPlate, Alert, AnalyticsLog
from utils.video_generator import generate_all_synthetic_videos

def seed_database(app):
    # Ensure directories exist
    os.makedirs(Config.SNAPSHOT_DIR, exist_ok=True)
    os.makedirs(Config.VIDEO_STORAGE_DIR, exist_ok=True)
    os.makedirs(Config.FACE_DB_DIR, exist_ok=True)
    
    # Generate test video files
    generate_all_synthetic_videos()
    
    with app.app_context():
        # Seed Cameras if none exist
        if Camera.query.count() == 0:
            print("[SEED] Seeding initial CCTV Camera feeds...")
            cam1 = Camera(
                name="BOP Alpha - Fence Sector 1",
                location="Sector 1 Perimeter (Night IR)",
                stream_url="SYNTHETIC_INTRUSION",
                camera_type="SYNTHETIC",
                is_active=True,
                night_mode=True
            )
            cam2 = Camera(
                name="Checkpost Bravo - Gate ANPR",
                location="Highway Checkpost Gate 2",
                stream_url="SYNTHETIC_ANPR",
                camera_type="SYNTHETIC",
                is_active=True,
                night_mode=False
            )
            cam3 = Camera(
                name="BOP Depot - Restricted Vault",
                location="Ammunition Depot Yard",
                stream_url="SYNTHETIC_LOITERING",
                camera_type="SYNTHETIC",
                is_active=True,
                night_mode=False
            )
            db.session.add_all([cam1, cam2, cam3])
            db.session.commit()
            print("[SEED] Created 3 initial Camera feeds.")

            # Seed Virtual Fences
            print("[SEED] Seeding Virtual Fence boundary zones...")
            fence1 = VirtualFence(
                camera_id=cam1.id,
                name="Forbidden Boundary Fence",
                fence_type="POLYGON",
                coordinates=json.dumps([[0.15, 0.40], [0.85, 0.25], [0.85, 0.70], [0.15, 0.85]]),
                trigger_objects="person,car,truck",
                is_active=True
            )
            fence3 = VirtualFence(
                camera_id=cam3.id,
                name="Depot Restricted Zone",
                fence_type="POLYGON",
                coordinates=json.dumps([[0.30, 0.35], [0.70, 0.35], [0.70, 0.80], [0.30, 0.80]]),
                trigger_objects="person",
                is_active=True
            )
            db.session.add_all([fence1, fence3])
            db.session.commit()

        # Seed Watchlist Plates if empty
        if WatchlistPlate.query.count() == 0:
            print("[SEED] Seeding Watchlist License Plates...")
            p1 = WatchlistPlate(
                plate_number="JK-02-C-9988",
                vehicle_info="Black SUV / Border Infiltrator Suspect",
                threat_level="CRITICAL",
                description="Suspect vehicle flagged for unauthorized movement in sector 4"
            )
            p2 = WatchlistPlate(
                plate_number="DL-01-AB-1234",
                vehicle_info="White Commercial Van",
                threat_level="HIGH",
                description="Stolen transport vehicle report"
            )
            db.session.add_all([p1, p2])
            db.session.commit()

        # Seed Watchlist Faces if empty
        if WatchlistFace.query.count() == 0:
            print("[SEED] Seeding Watchlist Target Faces...")
            f1 = WatchlistFace(
                person_name="Target Alpha (Suspect)",
                category="INFILTRATOR",
                image_path="/static/faces/suspect_alpha.jpg"
            )
            f2 = WatchlistFace(
                person_name="Target Bravo (POI)",
                category="SUSPECT",
                image_path="/static/faces/suspect_bravo.jpg"
            )
            db.session.add_all([f1, f2])
            db.session.commit()

        print("[SEED] Database seeding complete!")
