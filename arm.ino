#include <ESP32Servo.h>

Servo horizontalServo, shoulderServo, elbowServo, wristServo, magnetServo;
float horizontalValue = 0, shoulderValue = 105, elbowValue = 90, wristValue = 90, magnetValue = 90;

void setup() {
  Serial.begin(115200);
  horizontalServo.attach(13);   // change pins as needed
  shoulderServo.attach(14);
  elbowServo.attach(27);
  wristServo.attach(12);
  magnetServo.attach(26);
}

void loop() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    float s1, s2, s3, s4, s5;
    
    if (sscanf(data.c_str(), "%f,%f,%f,%f,%f", &s1, &s2, &s3, &s4, &s5) == 5) {
      horizontalValue = s1;  shoulderValue = s2;  elbowValue = s3, wristValue = s4, magnetValue = s5;

      horizontalValue = constrain(horizontalValue, 0, 180);
      shoulderValue = constrain(shoulderValue, 0, 180);
      elbowValue = constrain(elbowValue, 0, 180);
      wristValue = constrain(wristValue, 0, 180);
      magnetValue = constrain(magnetValue, 0, 180);
    }

    //int pulse = map(wristValue, 0, 180, 1000, 2000);
    //wristServo.writeMicroseconds(pulse);

    horizontalServo.write(horizontalValue);
    shoulderServo.write(shoulderValue);
    elbowServo.write(elbowValue);
    wristServo.write(wristValue);
    magnetServo.write(magnetValue);
  }
}
