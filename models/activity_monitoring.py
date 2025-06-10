import cv2
import numpy as np
from ultralytics import YOLO

class activity_monitoring:
    """
    Worker activity monitoring and classification system.
    Detects and classifies worker activities for productivity and safety analysis.
    """
    
    def __init__(self, model_path="yolov8n.pt", conf=0.70):
        self.model = YOLO(model_path)
        self.confidence = conf
        self.activity_classes = {
            'operating_machine': 'Operating Equipment',
            'idle': 'Idle/Standing',
            'walking': 'Walking/Moving',
            'using_phone': 'Using Phone',
            'maintenance': 'Maintenance Work',
            'lifting': 'Lifting/Carrying',
            'sitting': 'Sitting/Resting'
        }
        
    def classify_activity(self, person_box, frame):
        """Classify worker activity based on pose and context"""
        x1, y1, x2, y2 = person_box
        person_roi = frame[y1:y2, x1:x2]
        
        if person_roi.size == 0:
            return 'unknown'
        
        # Simple activity classification based on bounding box properties
        height = y2 - y1
        width = x2 - x1
        aspect_ratio = height / width if width > 0 else 0
        
        # Basic heuristics for activity classification
        if aspect_ratio > 2.5:
            return 'walking'
        elif aspect_ratio < 1.5:
            return 'sitting'
        elif width > height:
            return 'lifting'
        else:
            # Use color analysis for more specific activities
            roi_gray = cv2.cvtColor(person_roi, cv2.COLOR_BGR2GRAY)
            motion_intensity = np.std(roi_gray)
            
            if motion_intensity > 30:
                return 'operating_machine'
            elif motion_intensity < 10:
                return 'idle'
            else:
                return 'maintenance'
    
    def process(self, img, flag=True):
        """
        Process frame for activity monitoring
        Returns: (activities_detected, person_boxes, activities_list)
        """
        if not flag:
            return (False, [], [])
        
        person_boxes = []
        activities = []
        results = self.model(img, verbose=False)
        
        # Detect persons (class 0 in COCO dataset)
        for box in results[0].boxes:
            if int(box.cls[0]) == 0 and float(box.conf[0]) > self.confidence:  # Person class
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                person_boxes.append([x1, y1, x2, y2])
                
                # Classify activity
                activity = self.classify_activity([x1, y1, x2, y2], img)
                activities.append(activity)
                
                # Draw bounding box and activity label
                color = self.get_activity_color(activity)
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                
                activity_name = self.activity_classes.get(activity, activity.title())
                cv2.putText(img, activity_name, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        activities_detected = len(activities) > 0
        return (activities_detected, person_boxes, activities)
    
    def get_activity_color(self, activity):
        """Get color for different activities"""
        colors = {
            'operating_machine': (0, 255, 0),    # Green
            'idle': (255, 255, 0),               # Yellow
            'walking': (0, 255, 255),            # Cyan
            'using_phone': (0, 0, 255),          # Red
            'maintenance': (255, 0, 255),        # Magenta
            'lifting': (255, 165, 0),            # Orange
            'sitting': (128, 128, 128)           # Gray
        }
        return colors.get(activity, (255, 255, 255))