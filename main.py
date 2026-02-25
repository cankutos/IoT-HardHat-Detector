import cv2
import numpy as np
import socket
import time
import requests

# ==========================================
# ⚙️ SETTINGS (Your Information)
# ==========================================
ROBOT_IP = "192.168.1.15"            # <--- Set to .15 IP
ROBOT_PORT = 4210

# BLYNK SETTINGS
BLYNK_TOKEN = "hHq4bd6uq_1B7u0Og62xJnfPHLui7P99"  # <--- YOUR TOKEN
BLYNK_URL = "https://fra1.blynk.cloud/external/api/" 

# YELLOW HARD HAT COLOR RANGE (HSV)
HARDHAT_COLOR_LOWER = np.array([20, 100, 100]) 
HARDHAT_COLOR_UPPER = np.array([40, 255, 255]) 
# ==========================================

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
cap = cv2.VideoCapture(0)

# Status Variables
door_status = "CLOSED"
last_command_time = 0
last_blynk_send_time = 0

# Counters
violation_count = 0   
entry_count = 0   
status_led = 0      

# 🛡️ FILTER VARIABLES
is_person_processed = False 
validation_counter = 0        
REQUIRED_FRAMES = 8    # Time required for the loading bar to fill up

# Reset Message Variables
show_reset_message = False
reset_time = 0

def send_servo_command(angle):
    global last_command_time
    if time.time() - last_command_time > 0.2:
        try:
            msg = f"{angle},{angle}"
            sock.sendto(msg.encode(), (ROBOT_IP, ROBOT_PORT))
            last_command_time = time.time()
        except:
            pass

def update_blynk():
    try:
        link = f"{BLYNK_URL}batch/update?token={BLYNK_TOKEN}&V1={status_led}&V2={violation_count}&V3={entry_count}"
        requests.get(link, timeout=1)
        print(f"☁️ [IOT] UPDATED -> Violations:{violation_count} | Entries:{entry_count}")
    except:
        pass

def reset_system():
    global violation_count, entry_count, status_led, door_status, is_person_processed, validation_counter, show_reset_message, reset_time
    print("🔄 MANUAL RESET INITIATED...")
    violation_count = 0
    entry_count = 0
    status_led = 0
    door_status = "CLOSED"
    is_person_processed = False
    validation_counter = 0
    send_servo_command(0)
    update_blynk()
    show_reset_message = True
    reset_time = time.time()

print("🚀 SYSTEM STARTED: Fast Detection Mode")

while True:
    ret, frame = cap.read()
    if not ret: break
    
    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Face Detection
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=8, minSize=(60, 60))
    
    is_person_detected = False
    is_hardhat_detected = False
    
    # --- CONDITION 1: IF THERE IS A FACE ON SCREEN ---
    if len(faces) > 0:
        # Increment counter (Fill the green bar)
        if validation_counter <= REQUIRED_FRAMES:
            validation_counter += 1
        
        # Draw Loading Bar
        bar_length = int((validation_counter / REQUIRED_FRAMES) * 100)
        cv2.rectangle(frame, (20, 20), (20 + bar_length, 35), (0, 255, 0), -1)
        cv2.rectangle(frame, (20, 20), (120, 35), (255, 255, 255), 2) # Border

        # If counter is full, PROCESS THE PERSON
        if validation_counter >= REQUIRED_FRAMES:
            is_person_detected = True
            (x, y, w, h) = faces[0]
            
            # ROI (Region of Interest): Crop the top of the head
            hardhat_y1 = max(0, y - int(h * 0.6)) 
            hardhat_y2 = y
            hardhat_x1 = x
            hardhat_x2 = x + w
            hardhat_roi = frame[hardhat_y1:hardhat_y2, hardhat_x1:hardhat_x2]
            
            if hardhat_roi.size > 0:
                hsv_roi = cv2.cvtColor(hardhat_roi, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv_roi, HARDHAT_COLOR_LOWER, HARDHAT_COLOR_UPPER)
                yellow_ratio = cv2.countNonZero(mask) / (hardhat_roi.shape[0] * hardhat_roi.shape[1])
                
                if yellow_ratio > 0.15:
                    is_hardhat_detected = True
                    cv2.rectangle(frame, (hardhat_x1, hardhat_y1), (hardhat_x2, hardhat_y2), (0, 255, 0), 2)
                else:
                    cv2.rectangle(frame, (hardhat_x1, hardhat_y1), (hardhat_x2, hardhat_y2), (0, 0, 255), 2)
            
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 1)

    # --- CONDITION 2: IF NO ONE IS ON SCREEN (RESET!) ---
    else:
        # If no face, RESET the counter (Bar disappears)
        validation_counter = 0
        
        # If we previously processed someone and they left:
        if is_person_processed == True:
            print("👋 Person left, system ready for the next person.")
            is_person_processed = False  # Unlock
            door_status = "CLOSED"
            send_servo_command(0) # Close the door

    # --- DECISION MECHANISM ---
    if is_person_detected:
        # If person is not processed yet (Lock is Open)
        if is_person_processed == False:
            if is_hardhat_detected: 
                send_servo_command(90) 
                door_status = "OPEN"
                entry_count += 1
                status_led = 1   
                print("✅ NEW ENTRY!")
            else: 
                send_servo_command(0)  
                door_status = "CLOSED"
                violation_count += 1
                status_led = 0   
                print("⛔ NEW VIOLATION!")
            
            is_person_processed = True # Lock it
            update_blynk() 
            
        else:
            # Person is still on screen
            cv2.putText(frame, "PROCESSING COMPLETE", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            if is_hardhat_detected:
                cv2.putText(frame, "ACCESS GRANTED", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "PLEASE WEAR HARD HAT!", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    if show_reset_message:
        cv2.putText(frame, "SYSTEM RESET!", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)
        if time.time() - reset_time > 2:
            show_reset_message = False

    cv2.imshow("IOT SECURITY CAMERA", frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):
        reset_system()

cap.release()
cv2.destroyAllWindows()
