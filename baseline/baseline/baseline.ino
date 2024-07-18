#include <AFMotor.h>

AF_DCMotor motor1(1);
AF_DCMotor motor2(2);
AF_DCMotor motor3(3);
AF_DCMotor motor4(4);

unsigned long startTime = 0;
unsigned long runDuration = 0;
bool isRunning = false;

void setup() {
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();

    switch(command) {
      case 'w':
        setMotor(motor1, FORWARD, 100);
        setMotor(motor2, FORWARD, 100);
        setMotor(motor3, BACKWARD, 100);
        setMotor(motor4, BACKWARD, 100);
        break;
      case 's':
        setMotor(motor3, FORWARD, 100);
        setMotor(motor4, FORWARD, 100);
        setMotor(motor1, BACKWARD, 100);
        setMotor(motor2, BACKWARD, 100);
        break;
      case 'a':
        setAllMotors(FORWARD, 200);
        break;
      case 'd':
        setAllMotors(BACKWARD, 200);
        break;
      case 'x':
        stopAllMotors();
        break;
      case 'j':
        runForDistance(FORWARD, 50, 200);
        break;
      case 'l':
        runForDistance(BACKWARD, 50, 200);
        break;
      case 'i':
        runForDistanceCustom('w', 20, 100);
        break;
      case 'k':
        runForDistanceCustom('s', 20, 100);
        break;
    }
  }

  if (isRunning && (millis() - startTime >= runDuration)) {
    stopAllMotors();
    isRunning = false;
  }
}

void setMotor(AF_DCMotor &motor, uint8_t direction, int speed) {
  motor.setSpeed(speed);
  motor.run(direction);
}

void setAllMotors(uint8_t direction, int speed) {
  setMotor(motor1, direction, speed);
  setMotor(motor2, direction, speed);
  setMotor(motor3, direction, speed);
  setMotor(motor4, direction, speed);
}

void stopAllMotors() {
  motor1.run(RELEASE);
  motor2.run(RELEASE);
  motor3.run(RELEASE);
  motor4.run(RELEASE);
}

void runForDistance(uint8_t direction, int distance, int speed) {
  runDuration = convertDistanceToDuration(distance);
  setAllMotors(direction, speed);
  startTime = millis();
  isRunning = true;
}

void runForDistanceCustom(char command, int distance, int speed) {
  runDuration = convertDistanceToDuration(distance);

  if (command == 'w') {
    setMotor(motor1, FORWARD, speed);
    setMotor(motor2, FORWARD, speed);
    setMotor(motor3, BACKWARD, speed);
    setMotor(motor4, BACKWARD, speed);
  } else if (command == 's') {
    setMotor(motor3, FORWARD, speed);
    setMotor(motor4, FORWARD, speed);
    setMotor(motor1, BACKWARD, speed);
    setMotor(motor2, BACKWARD, speed);
  }

  startTime = millis();
  isRunning = true;
}

int convertDistanceToDuration(int distance) {
  // 假设速度与时间的关系为：distance = speed * time
  // 调整常数以适应实际情况。这里我们假设每单位距离需要10毫秒。
  int duration = distance * 10;
  return duration;
}
