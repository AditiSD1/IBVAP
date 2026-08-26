# Intelligent Border Video Analytics Platform (IBVAP)

**IBVAP** is an enterprise-grade AI-powered surveillance and video analytics platform engineered for border security, military outposts (BOPs), checkposts, and high-security facility perimeters. It provides real-time automated threat detection, multi-camera stream management, virtual fence intrusion tracking, automated license plate recognition (ANPR), facial recognition (FRS), loitering/speed anomaly detection, and instant alert notifications over WebSockets.

---

## Key Features

- **Multi-Camera Stream Management**: Ingests IP RTSP streams, USB webcams, recorded MP4 video files, and synthetic test streams with automatic low-latency MJPEG frame streaming.
- **AI Object Detection & Centroid Tracking**: Powered by Ultralytics YOLOv8 for human, vehicle, and object classification paired with custom centroid tracking for persistent identity, trajectory history, and speed anomaly analysis.
- **Virtual Fences & Intrusion Detection**: Interactive HTML5 Canvas tool (`fence_drawer.js`) for drawing polygon zones and tripwires. Features real-time ray-casting breach detection and loitering evaluation.
- **Night Vision Enhancement**: Automated CLAHE (Contrast Limited Adaptive Histogram Equalization) preprocessing pipeline for high-contrast thermal/IR night vision feed processing.
- **Automated License Plate Recognition (ANPR)**: Optical Character Recognition powered by EasyOCR for detecting and parsing vehicle license plates, automatically cross-referencing against suspect watchlists.
- **Facial Recognition System (FRS)**: Deep learning embedding comparison to match detected faces against watchlist threat categories (`SUSPECT`, `INFILTRATOR`, `VIP`, `AUTHORIZED`).
- **Real-Time Alert Engine**: WebSocket-driven instant alerts (`Flask-SocketIO`) with snapshot captures, severity categorization (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), and status tracking (`UNACKNOWLEDGED`, `ACKNOWLEDGED`, `RESOLVED`).
- **Analytics & Reporting Dashboard**: Hour-by-hour telemetry logging and graphical reporting of human counts, vehicle counts, fence breaches, ANPR hits, and night movement events.

---

## Tech Stack

- **Backend Framework**: Python 3.12, Flask, Flask-SQLAlchemy, Flask-SocketIO (Gevent/Threading async)
- **AI & Vision Pipeline**: PyTorch, OpenCV (`cv2`), Ultralytics YOLOv8, EasyOCR, NumPy
- **Database**: SQLite (`ibvap.db`) with SQLAlchemy ORM
- **Frontend Architecture**: HTML5, CSS3, Bootstrap 5 (Dark Security Theme), JavaScript (ES6+), HTML5 Canvas, Socket.IO Client, Chart.js
- **Testing**: Python `unittest` suite

---

## Project Structure

```
IBVAP/
├── app.py                      # Flask application setup, routes, WebSocket server & REST APIs
├── config.py                   # Global system parameters, storage paths & AI detection thresholds
├── database.py                 # SQLAlchemy database instance initialization
├── models.py                   # Database models (Camera, VirtualFence, Alert, Watchlist, etc.)
├── seed_data.py                # Database seeder & synthetic video initializer
├── yolov8n.pt                  # YOLOv8 nano pre-trained model weights
├── services/
│   ├── analytics_engine.py     # Core AI pipeline: YOLO detection, CentroidTracker, ANPR, FRS, night vision
│   └── stream_manager.py       # Multi-threaded camera frame capture workers & MJPEG generator
├── utils/
│   └── video_generator.py      # OpenCV utility to generate synthetic test streams for intrusion & ANPR
├── static/
│   ├── css/custom.css          # Custom dark UI styling & alert badges
│   ├── js/                     # Client-side scripts (main.js, fence_drawer.js)
│   ├── snapshots/              # Directory for auto-captured breach snapshot images
│   └── videos/                 # Storage for synthetic & recorded MP4 video feeds
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Base layout navigation bar & WebSocket alert listener
│   ├── index.html              # Main multi-camera live surveillance grid
│   ├── cameras.html            # Camera management & configuration dashboard
│   ├── virtual_fences.html     # Interactive fence drawer interface
│   ├── alerts.html             # Real-time alert log & status resolution hub
│   ├── watchlists.html         # ANPR plate & FRS suspect watchlist management
│   └── analytics.html          # Historical data & telemetry charts
└── tests/                      # Automated unit test suite
    ├── test_api.py             # REST API endpoint tests
    └── test_analytics.py       # Centroid tracker & fence detection algorithm tests
```

---

## Setup & Installation Instructions

### Prerequisites

- Python 3.10+ installed
- OpenCV dependencies & C++ build tools (for PyTorch/OpenCV support on Windows/Linux)
- Git

### 1. Clone the Repository
```bash
git clone <repository-url>
cd IBVAP
```

### 2. Set Up Virtual Environment (Recommended)
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
*(If `requirements.txt` is missing, install the core dependencies directly:)*
```bash
pip install flask flask-sqlalchemy flask-socketio opencv-python ultralytics easyocr torch torchvision numpy
```

### 4. Run the Application
Start the Flask application server:
```bash
python app.py
```
Upon the first run, `seed_data.py` automatically initializes the database (`ibvap.db`), generates synthetic test video streams (`static/videos/`), and starts background video ingestion threads.

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/cameras` | GET | Retrieve list of all registered cameras |
| `/api/cameras` | POST | Register a new RTSP stream, webcam, or video file feed |
| `/api/cameras/<id>/toggle_night` | PUT | Toggle low-light CLAHE night vision enhancement |
| `/api/fences` | GET | List virtual fence zones (filter by `camera_id`) |
| `/api/fences` | POST | Create or update a virtual fence polygon zone |
| `/api/fences/<id>` | DELETE | Remove a virtual fence zone |
| `/api/alerts` | GET | Retrieve alerts (filterable by `severity`, `status`, `camera_id`) |
| `/api/alerts/<id>/status` | PUT | Update alert status (`ACKNOWLEDGED` / `RESOLVED`) |
| `/api/watchlists/plates` | POST | Add a plate number to the ANPR watchlist |
| `/api/watchlists/plates/<id>` | DELETE | Remove plate from ANPR watchlist |
| `/api/watchlists/faces` | POST | Register a suspect face in FRS watchlist |
| `/api/stream/<camera_id>` | GET | Low-latency MJPEG video stream feed |

---

## Running Unit Tests

Execute the test suite using Python's built-in `unittest` runner:

```bash
python -m unittest discover tests
```

---

## Security & Deployment Considerations

- Change `SECRET_KEY` in `config.py` or set the `SECRET_KEY` environment variable prior to production deployment.
- For high-volume multi-camera setups (10+ feeds), a CUDA-capable NVIDIA GPU is recommended for optimal frame rates in YOLOv8 and EasyOCR processing.
- Ensure camera RTSP URLs are secured within isolated virtual private networks (VLANs).
