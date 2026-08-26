import cv2
import threading
import time
import os
from datetime import datetime
from config import Config
from models import Camera, VirtualFence, WatchlistFace, WatchlistPlate, Alert, db
from services.analytics_engine import ai_engine

class CameraStreamWorker(threading.Thread):
    def __init__(self, camera_id, app, socketio):
        super().__init__()
        self.camera_id = camera_id
        self.app = app
        self.socketio = socketio
        self.running = True
        self.latest_raw_frame = None
        self.latest_processed_frame = None
        self.lock = threading.Lock()

    def run(self):
        print(f"[STREAM MANAGER] Starting thread for Camera ID #{self.camera_id}")
        
        while self.running:
            with self.app.app_context():
                camera = db.session.get(Camera, self.camera_id)
                if not camera or not camera.is_active:
                    print(f"[STREAM MANAGER] Camera #{self.camera_id} deactivated or removed. Stopping stream worker.")
                    break
                    
                stream_url = camera.stream_url
                
                # Check for synthetic video feed keywords or RTSP / MP4 paths
                if stream_url == 'SYNTHETIC_INTRUSION':
                    stream_url = os.path.join(Config.VIDEO_STORAGE_DIR, 'border_fence_intrusion.mp4')
                elif stream_url == 'SYNTHETIC_ANPR':
                    stream_url = os.path.join(Config.VIDEO_STORAGE_DIR, 'checkpost_anpr.mp4')
                elif stream_url == 'SYNTHETIC_LOITERING':
                    stream_url = os.path.join(Config.VIDEO_STORAGE_DIR, 'bop_loitering.mp4')
                elif stream_url.isdigit():
                    stream_url = int(stream_url)  # USB webcam index (0, 1)

            cap = cv2.VideoCapture(stream_url)
            if not cap.isOpened():
                print(f"[STREAM MANAGER] Failed to open stream '{stream_url}' for Camera #{self.camera_id}. Retrying in 5s...")
                time.sleep(5.0)
                continue

            frame_delay = 1.0 / Config.PROCESSING_TARGET_FPS

            while self.running:
                loop_start = time.time()
                ret, frame = cap.read()
                
                # Loop video file continuously for uninterrupted surveillance demo
                if not ret:
                    if isinstance(stream_url, str) and stream_url.endswith(('.mp4', '.avi', '.mkv')):
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        print(f"[STREAM MANAGER] Stream disconnected for Camera #{self.camera_id}. Reconnecting...")
                        break

                # Fetch fresh DB entities for analytics rules
                with self.app.app_context():
                    camera_obj = db.session.get(Camera, self.camera_id)
                    if not camera_obj or not camera_obj.is_active:
                        self.running = False
                        break
                        
                    fences_list = VirtualFence.query.filter_by(camera_id=self.camera_id, is_active=True).all()
                    watchlist_faces = WatchlistFace.query.all()
                    watchlist_plates = WatchlistPlate.query.all()

                    # Run AI Analytics Engine
                    annotated_frame, triggered_alerts = ai_engine.process_camera_frame(
                        camera_obj, fences_list, watchlist_faces, watchlist_plates, frame
                    )

                    # Handle Triggered Alerts
                    for alert_data in triggered_alerts:
                        # Save snapshot image
                        ts_str = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                        snap_filename = f"alert_cam{self.camera_id}_{ts_str}.jpg"
                        snap_full_path = os.path.join(Config.SNAPSHOT_DIR, snap_filename)
                        snap_relative_path = f"/static/snapshots/{snap_filename}"
                        
                        cv2.imwrite(snap_full_path, annotated_frame)

                        # Create DB Alert record
                        alert_record = Alert(
                            camera_id=self.camera_id,
                            event_type=alert_data['event_type'],
                            severity=alert_data['severity'],
                            description=alert_data['description'],
                            snapshot_path=snap_relative_path,
                            status='UNACKNOWLEDGED'
                        )
                        db.session.add(alert_record)
                        db.session.commit()

                        # Broadcast alert via Socket.IO WebSocket to all connected clients
                        alert_dict = alert_record.to_dict()
                        self.socketio.emit('new_alert', alert_dict)
                        print(f"[ALERT TRIGGERED] Camera #{self.camera_id}: {alert_data['event_type']} ({alert_data['severity']})")

                # Store frames in memory for HTTP MJPEG streaming
                with self.lock:
                    self.latest_raw_frame = frame
                    self.latest_processed_frame = annotated_frame

                elapsed = time.time() - loop_start
                sleep_time = max(0.01, frame_delay - elapsed)
                time.sleep(sleep_time)

            cap.release()

    def get_jpeg_frame(self):
        with self.lock:
            if self.latest_processed_frame is None:
                # Return placeholder frame if stream warming up
                blank = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(blank, f"CONNECTING TO CAMERA #{self.camera_id}...", (100, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                _, jpeg = cv2.imencode('.jpg', blank)
                return jpeg.tobytes()
            _, jpeg = cv2.imencode('.jpg', self.latest_processed_frame)
            return jpeg.tobytes()

    def stop(self):
        self.running = False


class StreamManager:
    def __init__(self):
        self.workers = {} # camera_id -> CameraStreamWorker
        self.app = None
        self.socketio = None

    def init_app(self, app, socketio):
        self.app = app
        self.socketio = socketio

    def start_all_streams(self):
        with self.app.app_context():
            # Cap initial background camera workers to max 3 feeds to conserve RAM
            active_cameras = Camera.query.filter_by(is_active=True).limit(3).all()
            for cam in active_cameras:
                self.start_stream(cam.id)

    def start_stream(self, camera_id):
        if camera_id in self.workers and self.workers[camera_id].is_alive():
            return
        worker = CameraStreamWorker(camera_id, self.app, self.socketio)
        self.workers[camera_id] = worker
        worker.daemon = True
        worker.start()

    def stop_stream(self, camera_id):
        if camera_id in self.workers:
            self.workers[camera_id].stop()
            del self.workers[camera_id]

    def generate_mjpeg_stream(self, camera_id):
        if camera_id not in self.workers:
            self.start_stream(camera_id)
            time.sleep(0.5)

        worker = self.workers.get(camera_id)
        while True:
            if not worker:
                break
            frame_bytes = worker.get_jpeg_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.04) # ~25 FPS delivery to browser

stream_manager = StreamManager()
