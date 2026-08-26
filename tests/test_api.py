import unittest
import json
from app import app, db
from models import Camera, VirtualFence, Alert, WatchlistPlate

class TestFlaskAPI(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            # Seed test camera
            cam = Camera(
                name="Test BOP Cam",
                location="Sector 1",
                stream_url="SYNTHETIC_INTRUSION",
                camera_type="SYNTHETIC"
            )
            db.session.add(cam)
            db.session.commit()
            self.cam_id = cam.id

    def test_get_cameras(self):
        response = self.client.get('/api/cameras')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertGreaterEqual(len(data), 1)
        self.assertTrue(any(c['name'] == "Test BOP Cam" for c in data))

    def test_create_virtual_fence(self):
        payload = {
            'camera_id': self.cam_id,
            'name': 'Test Zone 1',
            'fence_type': 'POLYGON',
            'coordinates': [[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]],
            'trigger_objects': ['person', 'car']
        }
        response = self.client.post('/api/fences', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['name'], 'Test Zone 1')

    def test_analytics_summary(self):
        response = self.client.get('/api/analytics/summary')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('total_cameras', data)
        self.assertIn('critical_alerts', data)

if __name__ == '__main__':
    unittest.main()
