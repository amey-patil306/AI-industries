from ultralytics import YOLO
import cv2
from playsound import playsound
import threading

class smoke_detection:
    """
    Enhanced fire and smoke detection class for industrial safety monitoring.
    Detects both fire and smoke using YOLO model.
    """
    
    def __init__(self, model_path, conf=0.70, sound_path="./static/audio/fire_alarm.mp3"):
        self.model = YOLO(model_path)
        self.confidence = conf
        self.sound_path = sound_path
        self.last_alert_time = 0

    def play_alert_sound(self):
        """Play fire/smoke alert sound in separate thread"""
        threading.Thread(target=playsound, args=(self.sound_path,), daemon=True).start()

    def process(self, img, flag=True):
        """
        Process frame for fire and smoke detection
        Returns: (detection_found, bounding_boxes, detection_types)
        """
        if not flag:
            return (False, [], [])

        bb_boxes = []
        detection_types = []
        result = self.model(img, verbose=False)

        for box in result[0].boxes:
            if float(box.conf[0]) > self.confidence:
                bb = list(map(int, box.xyxy[0]))
                bb_boxes.append(bb)
                
                # Determine detection type based on class
                class_id = int(box.cls[0])
                if class_id == 0:  # Fire class
                    detection_types.append("fire")
                elif class_id == 1:  # Smoke class
                    detection_types.append("smoke")
                else:
                    detection_types.append("fire_smoke")

        if len(bb_boxes) > 0:
            found = True
            self.play_alert_sound()
            
            # Draw bounding boxes with labels
            for i, (box, det_type) in enumerate(zip(bb_boxes, detection_types)):
                x1, y1, x2, y2 = box
                color = (0, 0, 255) if det_type == "fire" else (0, 255, 255)  # Red for fire, Yellow for smoke
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                cv2.putText(img, det_type.upper(), (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        else:
            found = False
            
        return (found, bb_boxes, detection_types)