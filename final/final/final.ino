#include <AFMotor.h>
#include <Servo.h>

// 电机定义
AF_DCMotor motor1(1);
AF_DCMotor motor2(2);
AF_DCMotor motor3(3);
AF_DCMotor motor4(4);

// 舵机定义
Servo myServo;

// LED 引脚定义
const int redPin = 38;    // 红色引脚连接到数字38
const int greenPin = 40;  // 绿色引脚连接到数字40
const int bluePin = 42;   // 蓝色引脚连接到数字42

// 变量定义
unsigned long startTime = 0;
unsigned long runDuration = 0;
bool isRunning = false;
bool redLight = false;
bool servoMovePending = false;
bool startCommandActive = false;
bool continuousRun = false;
bool initialSpeedRun = false;
bool fCommandActive = false;

// 红蓝交替闪烁相关变量
bool toggleRedBlue = false;
unsigned long ledToggleTime = 0;
const unsigned long ledInterval = 500; // 闪烁间隔时间（毫秒）

void setup() {
  Serial.begin(9600);        // 初始化串口通信
  myServo.attach(36);        // 将舵机连接到引脚36

  // 设置LED引脚为输出模式
  pinMode(redPin, OUTPUT);   
  pinMode(greenPin, OUTPUT); 
  pinMode(bluePin, OUTPUT);  

  setColor(0, 255, 0);       // 默认显示绿色
}

void loop() {
  checkSerialInput();        // 检查串口输入

  // 检查是否到达运行时间
  if (isRunning && (millis() - startTime >= runDuration)) {
    stopAllMotors();         // 停止所有电机
    isRunning = false;       // 标记为停止状态
    if (startCommandActive) {
      servoMovePending = true; // 标记为需要旋转舵机
    }
    startTime = millis();    // 重置开始时间
  }

  // 检查是否需要旋转舵机
  if (servoMovePending && (millis() - startTime >= 2000)) {
    myServo.write(175);      // 舵机移动到175度
    servoMovePending = false; // 重置舵机移动标记
    startCommandActive = false; // 重置start命令标记
  }

  // 如果是初始速度运行模式
  if (initialSpeedRun && (millis() - startTime >= 1000)) { // 修改为1秒（1000毫秒）
    continuousRun = true;
    initialSpeedRun = false;
    startTime = millis();
  }

  // 如果是连续运行模式，所有电机以速度100持续运行
  if (continuousRun && !isRunning) {
    runAllMotors('w', 75); /*启动速度*/
  }

  // 红蓝交替闪烁
  if (redLight && (millis() - ledToggleTime >= ledInterval)) {
    if (toggleRedBlue) {
      setColor(255, 0, 0);  // 红色
    } else {
      setColor(0, 0, 255);  // 蓝色
    }
    toggleRedBlue = !toggleRedBlue; // 切换颜色
    ledToggleTime = millis(); // 重置LED切换时间
  }
}

// 检查串口输入
void checkSerialInput() {
  if (Serial.available() > 0) {  // 检查是否有串口输入
    String command = Serial.readStringUntil('\n');  // 读取串口输入

    // 根据输入命令进行操作
    if (command == "start1") {  
      redLight = true;      // 标记为红灯
      runForDistanceWithServo('w', 135, 80); // 前进30个单位，速度100
      startCommandActive = true; // 标记start命令活动
    } else if (command == "start2") {  
      redLight = true;      // 标记为红灯
      executeStart2Sequence();  // 执行 start2 命令序列
      startCommandActive = true; // 标记start命令活动
    } else if (command == "stop") {  
      setColor(0, 255, 0);  // 变回绿色
      redLight = false;     // 标记为绿灯
      stopAllMotors();      // 停止所有电机
      myServo.write(90);    // 舵机回到90度
      continuousRun = false; // 停止连续运行
      initialSpeedRun = false; // 停止初始速度运行
      fCommandActive = false; // 重置f命令活动标记
    } else if (command == "f") {
      if (!fCommandActive) {
        redLight = true;      // 标记为红灯
        initialSpeedRun = true; // 标记为初始速度运行
        continuousRun = false; // 确保连续运行标记未设置
        startTime = millis(); // 重置开始时间
        fCommandActive = true; // 标记f命令活动
      }
    } else {
      // 处理单个字符命令
      handleSingleCharCommand(command[0]);
    }
  }
}

// 执行 start2 命令序列
void executeStart2Sequence() {
  //runForDistanceCustom('w', 10, 100); // 前进10个单位，速度200
  //delay(convertDistanceToDuration(500)); // 添加延时
  runForDistance(BACKWARD, 10, 200); // 右转10个单位，速度200
  delay(convertDistanceToDuration(46)); // 添加延时
  //runForDistance(FORWARD, 10, 200); // 左转10个单位，速度200
  //delay(convertDistanceToDuration(58)); // 添加延时
  runForDistanceCustom('w', 10, 80); // 前进10个单位，速度200
  delay(convertDistanceToDuration(80)); // 添加延时
}

// 处理单个字符命令
void handleSingleCharCommand(char command) {
  if (!startCommandActive) { // 检查start命令是否活动
    if (continuousRun || initialSpeedRun) {
      // 停止所有电机的连续运行
      continuousRun = false;
      initialSpeedRun = false;
      stopAllMotors();
    }

    fCommandActive = false; // 重置f命令活动标记

    switch (command) {
      case 'w':
        runForDistanceCustom('w', 10, 200); // 前进10个单位，速度200
        break;
      case 's':
        runForDistanceCustom('s', 6, 250); // 后退6个单位，速度250
        break;
      case 'a':
        runForDistance(FORWARD, 10, 200); // 左转10个单位，速度200
        break;
      case 'd':
        runForDistance(BACKWARD, 10, 200); // 右转10个单位，速度200
        break;
      case 'q':
        runForDistance(FORWARD, 30, 200); // 左转30个单位，速度200
        break;
    }
  }
}

// 设置单个电机
void setMotor(AF_DCMotor &motor, uint8_t direction, int speed) {
  motor.setSpeed(speed);
  motor.run(direction);
}

// 设置所有电机
void setAllMotors(uint8_t direction, int speed) {
  setMotor(motor1, direction, speed);
  setMotor(motor2, direction, speed);
  setMotor(motor3, direction, speed);
  setMotor(motor4, direction, speed);
}

// 停止所有电机
void stopAllMotors() {
  motor1.run(RELEASE);
  motor2.run(RELEASE);
  motor3.run(RELEASE);
  motor4.run(RELEASE);
}

// 按距离运行
void runForDistance(uint8_t direction, int distance, int speed) {
  runDuration = convertDistanceToDuration(distance);
  setAllMotors(direction, speed);
  startTime = millis();
  isRunning = true;
}

// 自定义按距离运行
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

// 按距离运行并控制舵机
void runForDistanceWithServo(char command, int distance, int speed) {
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

// 所有电机运行
void runAllMotors(char command, int speed) {
  if (command == 'w') {
    setMotor(motor1, FORWARD, speed);
    setMotor(motor2, FORWARD, speed);
    setMotor(motor3, BACKWARD, speed);
    setMotor(motor4, BACKWARD, speed);
  }
  startTime = millis();
  isRunning = true;
}

// 将距离转换为持续时间
int convertDistanceToDuration(int distance) {
  // 假设距离和时间的关系：distance = speed * time
  // 调整常数以适应实际情况。这里假设每单位距离需要10毫秒。
  int duration = distance * 10;
  return duration;
}

// 设置LED颜色
void setColor(int red, int green, int blue) {
  analogWrite(redPin, red);     // 设置红色亮度
  analogWrite(greenPin, green); // 设置绿色亮度
  analogWrite(bluePin, blue);   // 设置蓝色亮度
}
