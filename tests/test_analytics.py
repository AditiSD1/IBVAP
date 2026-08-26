import unittest
import numpy as np
import cv2
import json

from services.analytics_engine import CentroidTracker, ai_engine
from config import Config

class TestAnalyticsEngine(unittest.TestCase):
    def test_centroid_tracker(self):
        tracker = CentroidTracker()
        rects = [[100, 100, 150, 200, 'person']]
        objects = tracker.update(rects)
        
        self.assertEqual(len(objects), 1)
        obj_id = list(objects.keys())[0]
        centroid, last_bbox = objects[obj_id]
        self.assertEqual(tuple(centroid), (125, 150))
        self.assertEqual(last_bbox[4], 'person')

    def test_virtual_fence_polygon_test(self):
        # Define 4-point polygon box from (100, 100) to (300, 300)
        pts = np.array([[100, 100], [300, 100], [300, 300], [100, 300]], np.int32).reshape((-1, 1, 2))
        
        # Test point inside (200, 200)
        inside = ai_engine.check_fence_breach((200, 200), pts)
        self.assertTrue(inside)
        
        # Test point outside (50, 50)
        outside = ai_engine.check_fence_breach((50, 50), pts)
        self.assertFalse(outside)

    def test_night_vision_preprocessing(self):
        # Create dummy dark frame
        dark_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        dark_frame[:, :] = (20, 20, 20)
        
        enhanced = ai_engine.preprocess_night_vision(dark_frame)
        self.assertEqual(enhanced.shape, dark_frame.shape)
        self.assertEqual(enhanced.dtype, np.uint8)

if __name__ == '__main__':
    unittest.main()
