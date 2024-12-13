
import cv2
import numpy as np
from pathlib import Path
import json

class SystemDetector:
    def __init__(self, min_area=5000, max_area=100000):
        self.min_area = min_area
        self.max_area = max_area
        self.annotations_file = Path('system_annotations.json')
        self.load_annotations()

    def load_annotations(self):
        if self.annotations_file.exists():
            with open(self.annotations_file, 'r') as f:
                self.annotations = json.load(f)
        else:
            self.annotations = {}

    def save_annotations(self):
        with open(self.annotations_file, 'w') as f:
            json.dump(self.annotations, f)

    def detect_systems(self, image_path):
        # Load image
        image = cv2.imread(str(image_path))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Check if we have manual annotations
        if str(image_path) in self.annotations:
            return len(self.annotations[str(image_path)]), image
            
        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area and shape
        systems = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if self.min_area < area < self.max_area:
                # Approximate the contour to a polygon
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
                
                # If it has 4 vertices, it's likely a system UI rectangle
                if len(approx) == 4:
                    systems.append(cnt)
                    cv2.drawContours(image, [cnt], -1, (0, 255, 0), 2)
        
        return len(systems), image

    def add_manual_annotation(self, image_path, boxes):
        """
        Add manual annotation for an image
        boxes: list of [x, y, width, height]
        """
        self.annotations[str(image_path)] = boxes
        self.save_annotations()
