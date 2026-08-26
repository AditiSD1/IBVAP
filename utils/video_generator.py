import os
import cv2
import numpy as np
import random

def ensure_dirs():
    video_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'videos')
    os.makedirs(video_dir, exist_ok=True)
    return video_dir

def create_synthetic_intrusion_video(output_path, num_frames=200):
    """
    Generates a simulated night-vision border perimeter feed with a walking human intruder crossing a fence.
    """
    width, height = 640, 480
    fps = 20
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Coordinates of intruder walking path (moving from top right across yellow border line to bottom left)
    start_x, start_y = 520, 100
    end_x, end_y = 150, 380
    
    for i in range(num_frames):
        t = i / float(num_frames)
        curr_x = int(start_x + (end_x - start_x) * t)
        curr_y = int(start_y + (end_y - start_y) * t)
        
        # Base low-light / night IR background (greenish tint + grain)
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :] = (15, 35, 15)  # Dark green tint typical of IR night vision
        
        # Add static background features (border post tower, fence posts, ground texture)
        cv2.rectangle(frame, (50, 50), (120, 220), (25, 55, 25), -1)  # Guard tower
        cv2.putText(frame, "BOP TOWER", (52, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80, 180, 80), 1)
        
        # Draw physical fence line graphic (gray mesh line)
        cv2.line(frame, (100, 300), (550, 200), (80, 120, 80), 3)
        for fx in range(100, 550, 40):
            fy = int(300 + (200 - 300) * ((fx - 100) / 450.0))
            cv2.line(frame, (fx, fy - 25), (fx, fy + 25), (80, 120, 80), 2)
        
        # Draw walking human synthetic figure (head, body, legs)
        body_color = (180, 220, 180)  # IR heat signature brightness
        # Head
        cv2.circle(frame, (curr_x, curr_y - 35), 10, body_color, -1)
        # Torso
        cv2.rectangle(frame, (curr_x - 12, curr_y - 25), (curr_x + 12, curr_y + 10), body_color, -1)
        # Arms
        arm_swing = int(8 * np.sin(i * 0.4))
        cv2.line(frame, (curr_x - 12, curr_y - 20), (curr_x - 20, curr_y + arm_swing), body_color, 4)
        cv2.line(frame, (curr_x + 12, curr_y - 20), (curr_x + 20, curr_y - arm_swing), body_color, 4)
        # Legs
        leg_stride = int(12 * np.sin(i * 0.4))
        cv2.line(frame, (curr_x - 6, curr_y + 10), (curr_x - 6 + leg_stride, curr_y + 40), body_color, 5)
        cv2.line(frame, (curr_x + 6, curr_y + 10), (curr_x + 6 - leg_stride, curr_y + 40), body_color, 5)
        
        # Add random IR thermal noise/grain
        noise = np.random.randint(0, 20, (height, width, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)
        
        # Add timestamp and stream header
        cv2.putText(frame, f"CAM-01 [BOP ALPHA FENCE] IR NIGHT | FRAME {i}", (15, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
        
        out.write(frame)
        
    out.release()
    print(f"[SYNTH] Generated intrusion video: {output_path}")

def create_synthetic_anpr_video(output_path, num_frames=200):
    """
    Generates a simulated vehicle checkpost feed with approaching vehicle and license plate.
    """
    width, height = 640, 480
    fps = 20
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    plate_text = "JK-02-C-9988"  # High threat license plate
    
    for i in range(num_frames):
        frame = np.ones((height, width, 3), dtype=np.uint8) * 50
        
        # Road asphalt background
        cv2.rectangle(frame, (120, 0), (520, 480), (35, 35, 35), -1)
        # Road markings
        for y_dash in range(0, 480, 40):
            cv2.line(frame, (320, y_dash), (320, y_dash + 20), (255, 255, 255), 2)
            
        # Checkpost barrier gate
        cv2.line(frame, (120, 320), (450, 320), (0, 0, 255), 6) # Red barrier pole
        cv2.putText(frame, "BORDER CHECKPOST STOP", (130, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # Vehicle moving towards barrier (scaling up)
        progress = i / float(num_frames)
        # Vehicle stays stationary near barrier in second half
        v_t = min(progress * 1.6, 1.0)
        
        car_y = int(50 + 200 * v_t)
        scale = 0.5 + 0.5 * v_t
        car_w = int(180 * scale)
        car_h = int(120 * scale)
        car_x = 320 - car_w // 2
        
        # Draw vehicle body (SUV/Truck)
        cv2.rectangle(frame, (car_x, car_y), (car_x + car_w, car_y + car_h), (30, 80, 160), -1)
        cv2.rectangle(frame, (car_x, car_y), (car_x + car_w, car_y + car_h), (200, 200, 200), 2)
        # Windshield
        cv2.rectangle(frame, (car_x + int(15*scale), car_y + int(15*scale)), 
                      (car_x + car_w - int(15*scale), car_y + int(45*scale)), (100, 150, 200), -1)
        # Headlights
        cv2.circle(frame, (car_x + int(20*scale), car_y + car_h - int(15*scale)), int(10*scale), (255, 255, 200), -1)
        cv2.circle(frame, (car_x + car_w - int(20*scale), car_y + car_h - int(15*scale)), int(10*scale), (255, 255, 200), -1)
        
        # Draw License Plate Box (White background with black text)
        plate_w = int(110 * scale)
        plate_h = int(30 * scale)
        plate_x = 320 - plate_w // 2
        plate_y = car_y + car_h - int(25 * scale)
        
        cv2.rectangle(frame, (plate_x, plate_y), (plate_x + plate_w, plate_y + plate_h), (255, 255, 255), -1)
        cv2.rectangle(frame, (plate_x, plate_y), (plate_x + plate_w, plate_y + plate_h), (0, 0, 0), 1)
        
        # Plate Text
        font_scale = 0.4 * scale
        cv2.putText(frame, plate_text, (plate_x + int(5*scale), plate_y + int(20*scale)),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), 2)
        
        # Stream Header
        cv2.putText(frame, f"CAM-02 [CHECKPOST BRAVO] ANPR | FRAME {i}", (15, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        
        out.write(frame)
        
    out.release()
    print(f"[SYNTH] Generated ANPR video: {output_path}")

def create_synthetic_loitering_video(output_path, num_frames=200):
    """
    Generates a video of a person loitering inside a restricted zone.
    """
    width, height = 640, 480
    fps = 20
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Restricted zone bounds: x (200..440), y (180..380)
    # Person enters at frame 20, loiters in zone until frame 180
    
    for i in range(num_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :] = (40, 40, 40)
        
        # Draw background building
        cv2.rectangle(frame, (100, 50), (540, 400), (70, 70, 70), -1)
        cv2.putText(frame, "BOP AMMUNITION DEPOT - RESTRICTED", (150, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # Person position
        if i < 30:
            px, py = 80 + i * 4, 250
        elif i > 170:
            px, py = 320 + (i - 170) * 4, 250
        else:
            # Small loitering pacing motion back and forth inside zone
            px = 300 + int(30 * np.sin((i - 30) * 0.1))
            py = 250 + int(15 * np.cos((i - 30) * 0.08))
            
        # Draw human target
        cv2.circle(frame, (px, py - 30), 12, (200, 150, 100), -1)  # Head
        cv2.rectangle(frame, (px - 14, px - 14 + 28), (py - 18, py + 25), (100, 80, 200), -1) # Body
        cv2.rectangle(frame, (px - 14, py - 18), (px + 14, py + 25), (60, 60, 180), -1)
        cv2.line(frame, (px - 8, py + 25), (px - 8, py + 55), (40, 40, 120), 4)
        cv2.line(frame, (px + 8, py + 25), (px + 8, py + 55), (40, 40, 120), 4)
        
        cv2.putText(frame, f"CAM-03 [BOP DEPOT RESTRICTED] LOITERING | FRAME {i}", (15, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        
        out.write(frame)
        
    out.release()
    print(f"[SYNTH] Generated loitering video: {output_path}")

def generate_all_synthetic_videos():
    v_dir = ensure_dirs()
    p1 = os.path.join(v_dir, 'border_fence_intrusion.mp4')
    p2 = os.path.join(v_dir, 'checkpost_anpr.mp4')
    p3 = os.path.join(v_dir, 'bop_loitering.mp4')
    
    if not os.path.exists(p1):
        create_synthetic_intrusion_video(p1)
    if not os.path.exists(p2):
        create_synthetic_anpr_video(p2)
    if not os.path.exists(p3):
        create_synthetic_loitering_video(p3)

if __name__ == '__main__':
    generate_all_synthetic_videos()
