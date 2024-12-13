
import cv2
import numpy as np
from pathlib import Path

class FrameAnalyzer:
    def __init__(self, frames_dir: Path, threshold=30, min_area=500):
        self.frames_dir = frames_dir
        self.threshold = threshold
        self.min_area = min_area
        from system_detector import SystemDetector
        self.system_detector = SystemDetector()
    
    def detect_changes(self):
        try:
            frames = sorted([f for f in self.frames_dir.glob('*.jpg') if not f.name.endswith('_analyzed.jpg')])
            action_frames = []
            
            if len(frames) < 2:
                return action_frames
                
            for i in range(len(frames)-1):
                try:
                    frame1 = cv2.imread(str(frames[i]))
                    frame2 = cv2.imread(str(frames[i+1]))
                    
                    if frame1 is None or frame2 is None:
                        continue
                        
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
                            num_systems, annotated_image = self.system_detector.detect_systems(str(frames[i+1]))
                            if annotated_image is not None:
                                output_path = str(frames[i+1]).replace('.jpg', '_analyzed.jpg')
                                cv2.imwrite(output_path, annotated_image)
                                action_frames.append((frames[i+1], num_systems))
                            break
                            
                except Exception as e:
                    print(f"Error processing frame {frames[i]}: {str(e)}")
                    continue
                    
            return action_frames
            
        except Exception as e:
            print(f"Error in detect_changes: {str(e)}")
            return []
