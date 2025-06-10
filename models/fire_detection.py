from ultralytics import YOLO
import cv2
from playsound import playsound
import threading

class fire_detection():
    
    def __init__(self, model_path, conf=0.85, sound_path="./static/audio/fire_alarm.mp3"):
        self.model = YOLO(model_path)
        self.confidence = conf
        self.sound_path = sound_path

    def play_alert_sound(self):
        threading.Thread(target=playsound, args=(self.sound_path,), daemon=True).start()

    def process(self, img, flag=True):
        if not flag:
            return (False, [])

        bb_boxes = []
        result = self.model(img, verbose=False)

        for box in result[0].boxes:
            if float(box.conf[0]) > self.confidence:
                bb = list(map(int, box.xyxy[0]))
                bb_boxes.append(bb)

        if len(bb_boxes):
            found = True
            self.play_alert_sound()  
        else:
            found = False
            
        return (found, bb_boxes)
