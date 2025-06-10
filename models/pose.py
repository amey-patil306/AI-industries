import cv2
import mediapipe as mp
import math
import numpy as np

# Constants
STRAIGHT_ARM_THRESHOLD = 160
VERTICAL_THRESH = 20
HORIZONTAL_THRESH = 25
MIN_VISIBILITY = 0.7

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba, bc = a - b, c - b
    angle = np.degrees(np.arctan2(bc[1], bc[0]) - np.arctan2(ba[1], ba[0]))
    angle = np.abs(angle)
    return 360 - angle if angle > 180 else angle

def get_arm_angle_vertical(shoulder, elbow):
    shoulder, elbow = np.array(shoulder), np.array(elbow)
    vec = elbow - shoulder
    angle_rad = math.atan2(vec[0], -vec[1])
    return math.degrees(angle_rad)

def detect_l_pose(frame):
    image = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    rgb.flags.writeable = False
    results = pose.process(rgb)
    rgb.flags.writeable = True
    frame = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    detected = False
    if results.pose_landmarks:
        lm = results.pose_landmarks.landmark
        try:
            ls, rs = lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value], lm[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            le, re = lm[mp_pose.PoseLandmark.LEFT_ELBOW.value], lm[mp_pose.PoseLandmark.RIGHT_ELBOW.value]
            lw, rw = lm[mp_pose.PoseLandmark.LEFT_WRIST.value], lm[mp_pose.PoseLandmark.RIGHT_WRIST.value]

            visible = all(p.visibility > MIN_VISIBILITY for p in [ls, rs, le, re, lw, rw])
            if visible:
                ls_c, rs_c = [ls.x, ls.y], [rs.x, rs.y]
                le_c, re_c = [le.x, le.y], [re.x, re.y]
                lw_c, rw_c = [lw.x, lw.y], [rw.x, rw.y]

                left_angle = calculate_angle(ls_c, le_c, lw_c)
                right_angle = calculate_angle(rs_c, re_c, rw_c)
                left_vert = get_arm_angle_vertical(ls_c, le_c)
                right_vert = get_arm_angle_vertical(rs_c, re_c)

                is_ls = left_angle > STRAIGHT_ARM_THRESHOLD
                is_rs = right_angle > STRAIGHT_ARM_THRESHOLD
                is_lv = abs(left_vert) <= VERTICAL_THRESH or abs(abs(left_vert) - 180) <= VERTICAL_THRESH
                is_rv = abs(right_vert) <= VERTICAL_THRESH or abs(abs(right_vert) - 180) <= VERTICAL_THRESH
                is_lh = abs(abs(left_vert) - 90) <= HORIZONTAL_THRESH
                is_rh = abs(abs(right_vert) - 90) <= HORIZONTAL_THRESH

                if (is_lv and is_rh and is_ls and is_rs) or (is_rv and is_lh and is_rs and is_ls):
                    detected = True
                    cv2.putText(frame, "L POSE DETECTED", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
        except Exception as e:
            print(f"Error processing landmarks: {e}")

    mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
    return frame, detected

# ✅ Wrap it in a class to match gear/fire interface
class pose_detection:
    def __init__(self):
        pass

    def process(self, img, flag=False):
        if not flag:
            return False, []
        frame, detected = detect_l_pose(img)
        if detected:
            # Dummy bounding box: full frame
            return True, [[0, 0, img.shape[1], img.shape[0]]]
        else:
            return False, []
