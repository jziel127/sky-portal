#include <Servo.h>

Servo photonServo;
Servo colorServo;

void setup() {
  Serial.begin(9600);
  photonServo.attach(9);   // signal wire to pin 9
  colorServo.attach(10);   // signal wire to pin 10
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');

    if (cmd.startsWith("PHOTON:")) {
      int value = cmd.substring(7).toInt();     // 0-100
      int angle = map(value, 0, 100, 0, 180);    // convert to servo angle
      photonServo.write(angle);
      Serial.println("OK: PHOTON " + String(value));
    }

    if (cmd.startsWith("COLOR:")) {
      int value = cmd.substring(6).toInt();
      int angle = map(value, 0, 100, 0, 180);
      colorServo.write(angle);
      Serial.println("OK: COLOR " + String(value));
    }
  }
}