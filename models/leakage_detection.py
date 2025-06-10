import cv2
import numpy as np
from ultralytics import YOLO

class leakage_detection:
    """
    Leakage detection for oil, gas, and water using computer vision.
    Detects visual anomalies and color changes indicating leaks.
    """
    
    def __init__(self, model_path="yolov8n.pt", conf=0.65):
        self.model = YOLO(model_path)
        self.confidence = conf
        self.leak_colors = {
            'oil': [(0, 0, 0), (50, 50, 50)],      # Dark colors for oil
            'water': [(100, 150, 150), (150, 255, 255)],  # Blue-ish for water
            'gas': [(200, 200, 200), (255, 255, 255)]     # Light colors for gas
        }
        
    def detect_color_anomalies(self, frame):
        """Detect color anomalies that might indicate leaks"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Define color ranges for different leak types
        leak_masks = {}
        
        # Oil leak detection (dark spots)
        lower_oil = np.array([0, 0, 0])
        upper_oil = np.array([180, 255, 50])
        leak_masks['oil'] = cv2.inRange(hsv, lower_oil, upper_oil)
        
        # Water leak detection (blue-ish areas)
        lower_water = np.array([100, 50, 50])
        upper_water = np.array([130, 255, 255])
        leak_masks['water'] = cv2.inRange(hsv, lower_water, upper_water)
        
        # Gas leak detection (using edge detection for distortion)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        leak_masks['gas'] = edges
        
        return leak_masks
    
    def process(self, img, flag=True):
        """
        Process frame for leakage detection
        Returns: (leak_detected, bounding_boxes, leak_type)
        """
        if not flag:
            return (False, [], 'none')
        
        leak_detected = False
        bounding_boxes = []
        detected_leak_type = 'none'
        
        # Color-based anomaly detection
        leak_masks = self.detect_color_anomalies(img)
        
        for leak_type, mask in leak_masks.items():
            # Find contours in the mask
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Minimum area threshold
                    x, y, w, h = cv2.boundingRect(contour)
                    bounding_boxes.append([x, y, x+w, y+h])
                    leak_detected = True
                    detected_leak_type = leak_type
                    
                    # Draw bounding box and label
                    color = (0, 0, 255) if leak_type == 'oil' else (255, 0, 0) if leak_type == 'water' else (0, 255, 255)
                    cv2.rectangle(img, (x, y), (x+w, y+h), color, 2)
                    cv2.putText(img, f"{leak_type.upper()} LEAK", (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Additional thermal-based detection (simulated)
        if not leak_detected:
            # Simulate thermal anomaly detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (15, 15), 0)
            
            # Find temperature anomalies (bright or dark spots)
            _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # Larger threshold for thermal anomalies
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Filter based on shape (leaks tend to be irregular)
                    if 0.3 < aspect_ratio < 3.0:
                        bounding_boxes.append([x, y, x+w, y+h])
                        leak_detected = True
                        detected_leak_type = 'thermal_anomaly'
                        
                        cv2.rectangle(img, (x, y), (x+w, y+h), (255, 255, 0), 2)
                        cv2.putText(img, "THERMAL ANOMALY", (x, y-10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        return (leak_detected, bounding_boxes, detected_leak_type)