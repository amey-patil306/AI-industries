from ultralytics import YOLO
import cv2

class enhanced_gear_detection:
    """
    Enhanced safety gear detection class for comprehensive PPE monitoring.
    Detects helmets, safety vests, gloves, boots, and other safety equipment.
    """
    
    def __init__(self, model_path, conf=0.75):
        self.model = YOLO(model_path)
        self.confidence = conf
        self.gear_classes = {
            0: "person",
            1: "helmet", 
            2: "safety_vest",
            3: "gloves",
            4: "safety_boots",
            5: "goggles",
            6: "mask"
        }
        self.required_gear = ["helmet", "safety_vest"]  # Minimum required PPE
        
    def check_compliance(self, detections):
        """
        Check if detected person has required safety gear
        Returns compliance status and missing gear
        """
        persons = []
        gear_items = []
        
        for detection in detections:
            class_name = self.gear_classes.get(detection['class'], 'unknown')
            if class_name == "person":
                persons.append(detection)
            else:
                gear_items.append(detection)
        
        compliance_results = []
        
        for person in persons:
            person_gear = []
            px1, py1, px2, py2 = person['bbox']
            
            # Check which gear items are near this person
            for gear in gear_items:
                gx1, gy1, gx2, gy2 = gear['bbox']
                
                # Simple proximity check - gear should overlap or be close to person
                if (gx1 < px2 and gx2 > px1 and gy1 < py2 and gy2 > py1):
                    person_gear.append(self.gear_classes[gear['class']])
            
            # Check compliance
            missing_gear = [gear for gear in self.required_gear if gear not in person_gear]
            is_compliant = len(missing_gear) == 0
            
            compliance_results.append({
                'person_bbox': person['bbox'],
                'detected_gear': person_gear,
                'missing_gear': missing_gear,
                'compliant': is_compliant
            })
        
        return compliance_results

    def process(self, img, flag=True):
        """
        Process frame for enhanced safety gear detection
        Returns: (violations_found, bounding_boxes, compliance_data)
        """
        if not flag:
            return (False, [], [])

        detections = []
        bb_boxes = []
        result = self.model(img, verbose=False)

        # Extract all detections
        for box in result[0].boxes:
            if float(box.conf[0]) > self.confidence:
                bbox = list(map(int, box.xyxy[0]))
                class_id = int(box.cls[0])
                
                detections.append({
                    'bbox': bbox,
                    'class': class_id,
                    'confidence': float(box.conf[0])
                })
                bb_boxes.append(bbox)

        # Check compliance for each person
        compliance_results = self.check_compliance(detections)
        violations_found = any(not result['compliant'] for result in compliance_results)
        
        # Draw bounding boxes and compliance status
        for result in compliance_results:
            x1, y1, x2, y2 = result['person_bbox']
            
            if result['compliant']:
                # Green box for compliant person
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(img, "PPE COMPLIANT", (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                # Red box for non-compliant person
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                missing_text = f"MISSING: {', '.join(result['missing_gear'])}"
                cv2.putText(img, "PPE VIOLATION", (x1, y1-25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                cv2.putText(img, missing_text, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        # Draw detected gear items
        for detection in detections:
            if detection['class'] != 0:  # Not a person
                x1, y1, x2, y2 = detection['bbox']
                gear_name = self.gear_classes.get(detection['class'], 'gear')
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 255, 0), 1)
                cv2.putText(img, gear_name.upper(), (x1, y1-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

        return (violations_found, bb_boxes, compliance_results)