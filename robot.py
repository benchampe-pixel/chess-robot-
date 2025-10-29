import serial
import time
from config import SERIAL_PORT, BAUD_RATE
import math

# rotational base
# these servos go from 0-180 degrees where 90 is the middle (straight)
horizontal_value = 90
shoulder_value = 90
elbow_value = 90

shoulder_length = 177.8; # in mm
elbow_length = 151.13 # in mm

ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
time.sleep(2)

def send_command(hor_servo, shoulder, elbow):
    global horizontal_value, shoulder_value, elbow_value

    horizontal_value += hor_servo
    shoulder_value += shoulder
    elbow_value += elbow
    
    ser.write(f"{horizontal_value:.2f},{shoulder_value:.2f},{elbow_value:.2f}\n".encode('utf-8'))

def go_to_point(x, y, z):
    global horizontal_value, shoulder_value, elbow_value

    # Arm segment lengths
    L1 = shoulder_length
    L2 = elbow_length

    # Horizontal base rotation (around Z axis)
    horizontal_angle = math.degrees(math.atan2(y, x))

    # Projected distance from base to target in horizontal plane
    r = math.sqrt(x**2 + y**2)

    # Vertical inverse kinematics for 2-link arm
    d = math.sqrt(r**2 + z**2)
    if d > L1 + L2 or d < abs(L1 - L2):
        print("Target out of reach.")
        return

    # Elbow angle using cosine law
    cos_elbow = (L1**2 + L2**2 - d**2) / (2 * L1 * L2)
    elbow_angle = math.degrees(math.acos(cos_elbow))

    # Shoulder angle relative to horizontal
    cos_shoulder = (d**2 + L1**2 - L2**2) / (2 * d * L1)
    shoulder_inner = math.degrees(math.acos(cos_shoulder))
    shoulder_base = math.degrees(math.atan2(z, r))
    shoulder_angle = shoulder_base + shoulder_inner

    # Map to servo coordinates (assuming 90° = straight)
    horizontal_servo = horizontal_angle
    shoulder_servo = 90 - shoulder_angle
    elbow_servo = 180 - elbow_angle  # bend decreases value

    # Send command
    ser.write(f"{horizontal_servo:.2f},{shoulder_servo:.2f},{elbow_servo:.2f}\n".encode('utf-8'))

    # Update stored values
    horizontal_value = horizontal_servo
    shoulder_value = shoulder_servo
    elbow_value = elbow_servo

def close_serial():
    ser.close()
