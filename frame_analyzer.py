
import cv2
import numpy as np
from pathlib import Path

class FrameAnalyzer:
    def __init__(self, frames_dir: Path, threshold=30, min_area=500):
        self.frames_dir = frames_dir
        self.threshold = threshold
        self.min_area = min_area
    
    def detect_changes(self):
        frames = sorted([f for f in self.frames_dir.glob('*.jpg')])
        action_frames = []
        
        if len(frames) < 2:
            return action_frames
            
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
