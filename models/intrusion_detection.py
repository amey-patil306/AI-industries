import cv2
import numpy as np
from ultralytics import YOLO

class intrusion_detection:
    """
    Intrusion and unauthorized entry detection for restricted zones.
    Uses person detection and region boundary logic.
    """
    
    def __init__(self, model_path="yolov8n.pt", conf=0.60):
        self.model = YOLO(model_path)
        self.confidence = conf
        self.restricted_zones = []
        
    def set_restricted_zone(self, points):
        """
        Set restricted zone polygon points
        points: list of (x, y) coordinates defining the restricted area
        """
        self.restricted_zones = [np.array(points, dtype=np.int32)]
        
    def point_in_polygon(self, point, polygon):
        """Check if a point is inside a polygon using ray casting algorithm"""
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def process(self, img, flag=True, restricted_zones=None):
        """
        Process frame for intrusion detection
        Returns: (intrusion_detected, person_boxes, intrusion_points)
        """
        if not flag:
            return (False, [], [])
            
        if restricted_zones:
            self.restricted_zones = [np.array(zone, dtype=np.int32) for zone in restricted_zones]
        
        person_boxes = []
        intrusion_points = []
        results = self.model(img, verbose=False)
        
        # Detect persons (class 0 in COCO dataset)
        for box in results[0].boxes:
            if int(box.cls[0]) == 0 and float(box.conf[0]) > self.confidence:  # Person class
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                person_boxes.append([x1, y1, x2, y2])
                
                # Check if person center point is in restricted zone
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                for zone in self.restricted_zones:
                    if self.point_in_polygon((center_x, center_y), zone):
                        intrusion_points.append((center_x, center_y))
                        # Draw red bounding box for intruder
                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3)
                        cv2.putText(img, "INTRUDER ALERT!", (x1, y1-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        break
                else:
                    # Draw green box for authorized person
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw restricted zones
        for zone in self.restricted_zones:
            cv2.polylines(img, [zone], True, (255, 0, 0), 2)
            cv2.putText(img, "RESTRICTED ZONE", tuple(zone[0]), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        intrusion_detected = len(intrusion_points) > 0
        return (intrusion_detected, person_boxes, intrusion_points)