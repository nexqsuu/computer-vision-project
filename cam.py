import cv2
import mediapipe as mp
import numpy as np
import time
from lasttest import VLCMediaPlayer
import tkinter as tk
import threading

# Mediapipe initialization
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils

# Default camera
cam = cv2.VideoCapture(0)
cam.set(3, 600)  # Set width (optional, depends on your camera)
cam.set(4, 600)  # Set height (optional, depends on your camera)

mode = [1]
job = ""

last_action_time = 0  # Tracks the timestamp of the last executed action
action_delay = 0.8  # Delay in seconds between actions

# function to detect raised fingers == modes
def detect_raised_fingers(hand_landmarks):
    fingers_raised = []
    # Define the landmark indices for fingertips and their corresponding joints
    finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
    finger_joints = [7, 11, 15, 19]
    
    for tip, joint in zip(finger_tips, finger_joints):
        # Check if the fingertip is above the joint
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[joint].y:
            fingers_raised.append(True)
        else:
            fingers_raised.append(False)

    return fingers_raised

def ccw(A, B, C):
    """Check if three points are in a counter-clockwise order."""
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

def do_lines_intersect(A, B, C, D):
    """Check if line segment AB intersects with line segment CD."""
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)
    
def process_camera(player):
    global last_action_time, job
    while True:
        success, frame = cam.read()
        current_time = time.time()
        if success:
            # Add mode text to the frame
            frame = cv2.flip(frame, 1)
            cv2.putText(frame, f'Modes: {mode[0]}', (10, 30), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f'job: {job}', (10, 70), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)

            # Convert BGR to RGB for Mediapipe processing
            RGB_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(RGB_frame)

            # Draw hand landmarks if detected
            if result.multi_hand_landmarks and result.multi_handedness:
                for hand_landmarks, hand_handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                    handedness_label = hand_handedness.classification[0].label  # 'Left' or 'Right'

                    if handedness_label == "Left":  # Check for a specific hand
                        fingers = detect_raised_fingers(hand_landmarks)
                        if sum(fingers) > 0:
                            mode.pop()
                            mode.append(sum(fingers))  # Count raised fingers


                        # Draw landmarks and connections
                        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    if handedness_label == "Right":  # Check for a specific hand
                        if current_time - last_action_time > action_delay:  # Check if delay has passed
                            if mode[0] == 1:
                                point_4 = (hand_landmarks.landmark[4].x, hand_landmarks.landmark[4].y)
                                point_3 = (hand_landmarks.landmark[3].x, hand_landmarks.landmark[3].y)
                                point_8 = (hand_landmarks.landmark[8].x, hand_landmarks.landmark[8].y)
                                point_7 = (hand_landmarks.landmark[7].x, hand_landmarks.landmark[7].y)

                                if do_lines_intersect(point_4, point_3, point_8, point_7):
                                    if player.is_playing():
                                        player.pause()
                                        print("pause")
                                    else:
                                        player.play()
                                        print("play")
                                    last_action_time = current_time
                                    job = "play/pause"
                           
                            elif mode[0] == 2:
                                thumb_tip = hand_landmarks.landmark[4]
                                index_tip = hand_landmarks.landmark[8]
                                distance = np.sqrt((thumb_tip.x - index_tip.x) ** 2 + (thumb_tip.y - index_tip.y) ** 2)
                                
                                # Map distance to volume
                                volume = int(np.interp(distance, [0.02, 0.1], [0, 100]))  # Scale appropriately
                                player.volume_slider.set(volume)
                                print(f"Volume: {volume}%")  # Connect this to system volume control
                                job = "volume"
                                last_action_time = current_time
                                
                            elif mode[0] == 3:
                                index_tip = hand_landmarks.landmark[8]
                                print(index_tip)
                                if index_tip.x < 0.3:
                                    player.fast_forward()
                                elif index_tip.x > 0.7:
                                    player.rewind()
                                job = "ff/rewind"
                                last_action_time = current_time
                                
                            elif mode[0] == 4:
                                control = detect_raised_fingers(hand_landmarks)
                                if sum(control) > 0:
                                        player.load_new_song()
                                job = "load new song"
                                last_action_time = current_time


                        # Draw landmarks and connections
                        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Display the processed frame
            cv2.imshow('Camera', frame)

        # Exit loop on pressing 'q'
        if cv2.waitKey(1) == ord('q'):
            break
        
if __name__ == "__main__":
    root = tk.Tk()
    player = VLCMediaPlayer(root)

    # Start camera processing in a separate thread
    camera_thread = threading.Thread(target=process_camera, args=(player,), daemon=True)
    camera_thread.start()

    # Start the Tkinter mainloop
    root.mainloop()
