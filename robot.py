import serial
import time
from config import SERIAL_PORT, BAUD_RATE

horizontal_value = 90
shoulder_value = 90
elbow_value = 90

ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
time.sleep(2)

def send_command(hor_servo, shoulder, elbow):
    global horizontal_value, shoulder_value, elbow_value

    horizontal_value += hor_servo
    shoulder_value += shoulder
    elbow_value += elbow
    
    ser.write(f"{horizontal_value:.2f},{shoulder_value:.2f},{elbow_value:.2f}\n".encode('utf-8'))

def close_serial():
    ser.close()
