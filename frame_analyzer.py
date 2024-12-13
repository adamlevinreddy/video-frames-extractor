
import cv2
import numpy as np
import gc
from pathlib import Path

class FrameAnalyzer:
    def __init__(self, frames_dir: Path, threshold=30, min_area=500, batch_size=10):
        self.frames_dir = frames_dir
        self.threshold = threshold
        self.min_area = min_area
        self.batch_size = batch_size
    
    def detect_changes(self):
        frames = sorted([f for f in self.frames_dir.glob('*.jpg')])
        action_frames = []
        
        if len(frames) < 2:
            return action_frames
            
        # Process frames in batches
        for i in range(0, len(frames)-1, self.batch_size):
            batch_end = min(i + self.batch_size, len(frames)-1)
            batch_frames = frames[i:batch_end]
            
            prev_frame = None
            for frame_path in batch_frames:
                frame = cv2.imread(str(frame_path))
                if frame is None:
                    continue
                    
                if prev_frame is not None:
                    # Convert to grayscale
                    gray1 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                    gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
                    # Calculate absolute difference
                    diff = cv2.absdiff(gray1, gray2)
                    
                    # Threshold the difference
                    _, thresh = cv2.threshold(diff, self.threshold, 255, cv2.THRESH_BINARY)
                    
                    # Find contours
                    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    # Check if any contour exceeds minimum area
                    for contour in contours:
                        if cv2.contourArea(contour) > self.min_area:
                            action_frames.append(frame_path)
                            break
                
                prev_frame = frame.copy()
                
            # Force garbage collection after each batch
            del prev_frame
            gc.collect()
            
        for i in range(len(frames)-1):
            frame1 = cv2.imread(str(frames[i]))
            frame2 = cv2.imread(str(frames[i+1]))
            
            # Convert to grayscale
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            
            # Calculate absolute difference
            diff = cv2.absdiff(gray1, gray2)
            
            # Threshold the difference
            _, thresh = cv2.threshold(diff, self.threshold, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Check if any contour exceeds minimum area
            for contour in contours:
                if cv2.contourArea(contour) > self.min_area:
                    action_frames.append(frames[i+1])
                    break
                    
        return action_frames
