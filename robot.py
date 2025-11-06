import serial
import time
from config import SERIAL_PORT, BAUD_RATE
import math

# rotational base
# these servos go from 0-180 degrees where 90 is the middle (straight)
horizontal_value = 90
shoulder_value = 90
elbow_value = 90
wrist_value = 90
magnet_value = 90

shoulder_length = 161.3; # in mm
elbow_length = 112.4 # in mm
wrist_length = 68.2 # in mm

ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
time.sleep(2)

def send_command(hor_servo, shoulder, elbow, wrist, magnet):
    global horizontal_value, shoulder_value, elbow_value, wrist_value, magnet_value

    horizontal_value += hor_servo
    shoulder_value += shoulder
    elbow_value += elbow
    wrist_value += wrist
    magnet_value += magnet

    # clamp values
    horizontal_value = max(0.0, min(180.0, horizontal_value))
    shoulder_value   = max(0.0, min(180.0, shoulder_value))
    elbow_value      = max(0.0, min(180.0, elbow_value))
    wrist_value      = max(0.0, min(180.0, wrist_value))
    magnet_value     = max(0.0, min(180.0, magnet_value))
    
    ser.write(f"{horizontal_value:.2f},{shoulder_value:.2f},{elbow_value:.2f},{wrist_value:.2f},{magnet_value:.2f}\n".encode('utf-8'))

def go_to_point(x, y, z, final_pitch_deg = 0, magnet_rotation = 0):
    global horizontal_value, shoulder_value, elbow_value, wrist_value, magnet_value

    # Arm segment lengths
    L1 = shoulder_length
    L2 = elbow_length
    L3 = wrist_length

    # Horizontal base rotation (around Z axis)
    horizontal_angle = math.degrees(math.atan2(y, x))

    # Projected distance from base to target in horizontal plane
    r = math.sqrt(x**2 + y**2)

    pitch_rad = math.radians(final_pitch_deg)
    wrist_x = r - L3 * math.cos(pitch_rad)
    wrist_z = z - L3 * math.sin(pitch_rad)
    d = math.sqrt(wrist_x**2 + wrist_z**2)

    # Vertical inverse kinematics for 2-link arm
    if d > L1 + L2 or d < abs(L1 - L2):
        print("Target out of reach.")
        return

    # Shoulder angle relative to horizontal
    cos_shoulder = (d**2 + L1**2 - L2**2) / (2 * d * L1)
    cos_shoulder = max(-1.0, min(1.0, cos_shoulder))
    shoulder_inner = math.degrees(math.acos(cos_shoulder))
    shoulder_base = math.degrees(math.atan2(wrist_z, wrist_x))
    shoulder_angle = shoulder_base + shoulder_inner

    # Map to servo coordinates (90* = straight)
    # Elbow angle using cosine law, internal angle between link1 and link2
    cos_elbow = (L1**2 + L2**2 - d**2) / (2 * L1 * L2)
    cos_elbow = max(-1.0, min(1.0, cos_elbow))  # numeric safety
    elbow_internal_deg = math.degrees(math.acos(cos_elbow))  # 0-180

    total_forearm_angle = shoulder_angle - (180 - elbow_internal_deg)
    wrist_angle = final_pitch_deg - total_forearm_angle

    # clamp to servo range
    horizontal_servo = max(0.0, min(180.0, horizontal_angle))
    shoulder_servo = max(0.0, min(180.0, 180 - shoulder_angle))
    elbow_servo = max(0.0, min(270.0, 180 - elbow_internal_deg))
    wrist_servo = max(0.0, min(180.0, 90 + wrist_angle))
    magnet_servo = max(0.0, min(180.0, magnet_rotation))
    # Map internal elbow angle to servo angle:

    # Send command
    ser.write(f"{horizontal_servo:.2f},{shoulder_servo:.2f},{elbow_servo:.2f},{wrist_servo:.2f},{magnet_servo:.2f}\n".encode('utf-8'))

    # Update stored values
    horizontal_value = horizontal_servo
    shoulder_value = shoulder_servo
    elbow_value = elbow_servo
    wrist_value = wrist_servo
    magnet_value = magnet_servo

def get_current_point():
    global horizontal_value, shoulder_value, elbow_value, wrist_value, magnet_value
    # Arm segment lengths
    L1 = shoulder_length
    L2 = elbow_length
    L3 = wrist_length

    # Convert servo angles back to physical joint angles
    horizontal_angle = math.radians(horizontal_value)
    shoulder_angle = math.radians(180 - shoulder_value)  # undo mapping
    elbow_internal = math.radians(180 - elbow_value)     # undo mapping
    wrist_angle = math.radians(wrist_value - 90)         # undo mapping

    # Find total vertical plane angle of the arm
    total_angle = shoulder_angle - (math.pi - elbow_internal)

    # 2D projection (r,z)
    r = L1 * math.cos(shoulder_angle) + L2 * math.cos(total_angle) + L3 * math.cos(total_angle + wrist_angle)
    z = L1 * math.sin(shoulder_angle) + L2 * math.sin(total_angle) + L3 * math.sin(total_angle + wrist_angle)

    # Rotate around Z-axis using horizontal angle
    x = r * math.cos(horizontal_angle)
    y = r * math.sin(horizontal_angle)

    return (x, y, z)
    
def close_serial():
    ser.close()
