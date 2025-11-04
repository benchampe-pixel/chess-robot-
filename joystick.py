import pygame
from config import MAX_SPEED, DEADZONE

class JoystickInput:
    lt_raw = 0
    rt_raw = 0
    left_y = 0
    right_y = 0

class JoystickController:
    def __init__(self):
        self.horServo = 0
        self.shoulder = 0
        self.elbow = 0

    def update(self, jsi: JoystickInput):
        lt = trigger_value(jsi.lt_raw)
        rt = trigger_value(jsi.rt_raw)

        self.horServo = (lt - rt) * MAX_SPEED

        if abs(jsi.left_y) < DEADZONE:
            jsi.left_y = 0
        self.shoulder = jsi.left_y * MAX_SPEED

        if abs(jsi.right_y) < DEADZONE:
            jsi.right_y = 0
        self.elbow = jsi.right_y * MAX_SPEED
        
        return self.horServo, self.shoulder, self.elbow

LEFT_TRIGGER = 4
RIGHT_TRIGGER = 5
LEFT_Y = 1
RIGHT_Y = 3
# LEFT_TRIGGER = 3
# RIGHT_TRIGGER = 2
# LEFT_Y = 1
# RIGHT_Y = 0

def trigger_value(raw):
    """Map trigger axis from [-1, 1] to [0, 1]"""
    return (raw + 1) / 2

def get_inputs(joystick):
    jsi = JoystickInput()
    jsi.lt_raw = joystick.get_axis(LEFT_TRIGGER)
    jsi.rt_raw = joystick.get_axis(RIGHT_TRIGGER)
    jsi.left_y = joystick.get_axis(LEFT_Y)
    jsi.right_y = joystick.get_axis(RIGHT_Y)

    return jsi