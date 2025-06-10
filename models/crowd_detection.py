import cv2
import numpy as np
from ultralytics import YOLO

class crowd_detection:
    """
    Crowd density monitoring and detection system.
    Monitors crowd density to prevent accidents and bottlenecks.
    """
    
    def __init__(self, model_path="yolov8n.pt", conf=0.60):
        self.model = YOLO(model_path)
        self.confidence = conf
        self.density_thresholds = {
            'low': 5,
            'medium': 10,
            'high': 15,
            'critical': 20
        }
        
    def calculate_density(self, person_boxes, frame_area):
        """Calculate crowd density based on person count and area"""
        person_count = len(person_boxes)
        density = person_count / (frame_area / 10000)  # Normalize by area
        
        if density < self.density_thresholds['low']:
            return 'low', person_count
        elif density < self.density_thresholds['medium']:
            return 'medium', person_count
        elif density < self.density_thresholds['high']:
            return 'high', person_count
        else:
            return 'critical', person_count
    
    def detect_bottlenecks(self, person_boxes, frame_shape):
        """Detect potential bottlenecks based on person clustering"""
        if len(person_boxes) < 3:
            return []
        
        # Convert boxes to center points
        centers = []
        for box in person_boxes:
            x1, y1, x2, y2 = box
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            centers.append([center_x, center_y])
        
        centers = np.array(centers)
        
        # Simple clustering to find dense areas
        bottlenecks = []
        cluster_radius = 100  # pixels
        
        for i, center in enumerate(centers):
            nearby_count = 0
            for j, other_center in enumerate(centers):
                if i != j:
                    distance = np.linalg.norm(center - other_center)
                    if distance < cluster_radius:
                        nearby_count += 1
            
            if nearby_count >= 3:  # Threshold for bottleneck
                bottlenecks.append({
                    'center': center,
                    'density': nearby_count,
                    'radius': cluster_radius
                })
        
        return bottlenecks
    
    def process(self, img, flag=True):
        """
        Process frame for crowd detection
        Returns: (crowd_alert, person_boxes, density_info)
        """
        if not flag:
            return (False, [], 'low')
        
        person_boxes = []
        results = self.model(img, verbose=False)
        
        # Detect persons (class 0 in COCO dataset)
        for box in results[0].boxes:
            if int(box.cls[0]) == 0 and float(box.conf[0]) > self.confidence:  # Person class
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                person_boxes.append([x1, y1, x2, y2])
                
                # Draw person bounding box
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 1)
        
        # Calculate crowd density
        frame_area = img.shape[0] * img.shape[1]
        density_level, person_count = self.calculate_density(person_boxes, frame_area)
        
        # Detect bottlenecks
        bottlenecks = self.detect_bottlenecks(person_boxes, img.shape)
        
        # Draw density information
        density_color = self.get_density_color(density_level)
        cv2.putText(img, f"People Count: {person_count}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(img, f"Density: {density_level.upper()}", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, density_color, 2)
        
        # Draw bottlenecks
        for bottleneck in bottlenecks:
            center = bottleneck['center']
            radius = bottleneck['radius']
            cv2.circle(img, tuple(center.astype(int)), radius, (0, 0, 255), 2)
            cv2.putText(img, "BOTTLENECK", (center[0]-50, center[1]), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Alert if density is high or critical, or if bottlenecks detected
        crowd_alert = density_level in ['high', 'critical'] or len(bottlenecks) > 0
        
        density_info = {
            'level': density_level,
            'count': person_count,
            'bottlenecks': len(bottlenecks)
        }
        
        return (crowd_alert, person_boxes, density_info)
    
    def get_density_color(self, density_level):
        """Get color for different density levels"""
        colors = {
            'low': (0, 255, 0),      # Green
            'medium': (0, 255, 255), # Yellow
            'high': (0, 165, 255),   # Orange
            'critical': (0, 0, 255)  # Red
        }
        return colors.get(density_level, (255, 255, 255))