import pygame
import serial
import time

# --- CONFIG ---
SERIAL_PORT = 'COM5'      # ESP32 port
BAUD_RATE = 115200
MAX_SPEED = 3.0           # degrees per update
DEADZONE = 0.1            # joystick deadzone

horizontal_value = 0
shoulder_value = 0
elbow_value = 0

# --- SETUP SERIAL ---
ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
time.sleep(2)

# --- SETUP CONTROLLER ---
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()
print("Controller connected:", joystick.get_name())

def trigger_value(raw):
    """Map trigger axis from [-1, 1] to [0, 1]"""
    return (raw + 1) / 2

class JoystickInput:
    lt_raw = 0
    rt_raw = 0
    left_y = 0
    right_y = 0

class JoystickController:
    def __init__(self, jsi: JoystickInput):
        self.horServo = jsi.lt_raw - jsi.rt_raw * MAX_SPEED
        self.shoulder = jsi.left_y * MAX_SPEED
        self.elbow = jsi.right_y * MAX_SPEED

    def update(self, jsi: JoystickInput):
        lt = trigger_value(jsi.lt_raw)
        rt = trigger_value(jsi.rt_raw)

        self.horServo = (lt - rt) * MAX_SPEED

        if abs(jsi.y_left) < DEADZONE:
            y_left = 0
        self.shoulder = y_left * MAX_SPEED

        if abs(jsi.y_right) < DEADZONE:
            y_right = 0
        self.elbow = y_right * MAX_SPEED

    def send(self):
        horizontal_value += self.horServo
        shoulder_value += self.shoulder
        elbow_value += self.elbow
        
        ser.write(f"{self.horServo:.2f},{self.shoulder:.2f},{self.elbow:.2f}\n".encode('utf-8'))

LEFT_TRIGGER = 4
RIGHT_TRIGGER = 5
LEFT_Y = 1
RIGHT_Y = 3

def get_inputs(joystick):
    jsi = JoystickInput
    jsi.lt_raw = joystick.get_axis(LEFT_TRIGGER)
    jsi.rt_raw = joystick.get_axis(RIGHT_TRIGGER)
    jsi.left_y = joystick.get_axis(LEFT_Y)
    jsi.right_y = joystick.get_axis(RIGHT_Y)

    return jsi

try:
    jsc = JoystickController(get_inputs(joystick))

    while True:
        pygame.event.pump()

        jsc.update(get_inputs(joystick))
        jsc.send()

        time.sleep(0.02)  # ~50 Hz loop

except KeyboardInterrupt:
    print("\nExiting...")
finally:
    ser.close()
    pygame.quit()
