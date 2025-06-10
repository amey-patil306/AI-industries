import cv2
import numpy as np
from ultralytics import YOLO

class defect_detection:
    """
    Product defect detection for assembly lines and manufacturing.
    Identifies defective products using image analysis and ML.
    """
    
    def __init__(self, model_path="yolov8n.pt", conf=0.80):
        self.model = YOLO(model_path)
        self.confidence = conf
        self.defect_types = {
            'scratch': 'Surface Scratch',
            'dent': 'Dent/Deformation',
            'discoloration': 'Color Defect',
            'crack': 'Crack/Break',
            'missing_part': 'Missing Component',
            'size_error': 'Size Deviation'
        }
        
    def detect_surface_defects(self, frame):
        """Detect surface defects using edge detection and contour analysis"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Morphological operations to connect broken edges
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        defects = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if 100 < area < 5000:  # Filter by area
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                # Classify defect type based on shape
                if aspect_ratio > 3:
                    defect_type = 'scratch'
                elif area < 500:
                    defect_type = 'crack'
                else:
                    defect_type = 'dent'
                
                defects.append({
                    'type': defect_type,
                    'bbox': [x, y, x+w, y+h],
                    'area': area
                })
        
        return defects
    
    def detect_color_defects(self, frame):
        """Detect color-based defects"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Define expected color range (this should be calibrated for specific products)
        lower_expected = np.array([0, 50, 50])
        upper_expected = np.array([180, 255, 255])
        
        # Create mask for expected colors
        mask = cv2.inRange(hsv, lower_expected, upper_expected)
        
        # Invert mask to find color anomalies
        color_defects = cv2.bitwise_not(mask)
        
        # Find contours of color defects
        contours, _ = cv2.findContours(color_defects, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        defects = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 200:
                x, y, w, h = cv2.boundingRect(contour)
                defects.append({
                    'type': 'discoloration',
                    'bbox': [x, y, x+w, y+h],
                    'area': area
                })
        
        return defects
    
    def process(self, img, flag=True):
        """
        Process frame for defect detection
        Returns: (defects_found, bounding_boxes, defect_details)
        """
        if not flag:
            return (False, [], [])
        
        all_defects = []
        bounding_boxes = []
        
        # Detect surface defects
        surface_defects = self.detect_surface_defects(img)
        all_defects.extend(surface_defects)
        
        # Detect color defects
        color_defects = self.detect_color_defects(img)
        all_defects.extend(color_defects)
        
        # Draw defects on image
        for defect in all_defects:
            x1, y1, x2, y2 = defect['bbox']
            bounding_boxes.append([x1, y1, x2, y2])
            
            # Color code by defect type
            color = self.get_defect_color(defect['type'])
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            
            defect_name = self.defect_types.get(defect['type'], defect['type'].title())
            cv2.putText(img, f"DEFECT: {defect_name}", (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        defects_found = len(all_defects) > 0
        return (defects_found, bounding_boxes, [d['type'] for d in all_defects])
    
    def get_defect_color(self, defect_type):
        """Get color for different defect types"""
        colors = {
            'scratch': (0, 255, 255),      # Yellow
            'dent': (0, 0, 255),           # Red
            'discoloration': (255, 0, 255), # Magenta
            'crack': (255, 0, 0),          # Blue
            'missing_part': (0, 255, 0),   # Green
            'size_error': (255, 255, 0)    # Cyan
        }
        return colors.get(defect_type, (255, 255, 255))