# Autonomous Underwater Robot - Setup Guide

## Hardware Setup

### 1. Raspberry Pi Setup
1. Connect the components to Raspberry Pi:
   ```
   MPU6050 (I2C):
   - VCC -> 3.3V
   - GND -> GND
   - SCL -> GPIO 3 (SCL)
   - SDA -> GPIO 2 (SDA)

   L298N Motor Drivers:

   L298N #1 (Forward/Backward Motors):
   - IN1 -> GPIO 17 (Forward)
   - IN2 -> GPIO 18 (Backward)
   - ENA -> GPIO 27 (Speed Control)
   - Motor power -> 12V from battery via buck converter

   L298N #2 (Up/Down Motors):
   - IN1 -> GPIO 22 (Up)
   - IN2 -> GPIO 23 (Down)
   - ENA -> GPIO 24 (Speed Control)
   - Motor power -> 12V from battery via buck converter

   Ultrasonic Sensors:
   Front Sensor:
   - TRIG -> GPIO 5
   - ECHO -> GPIO 25
   - VCC -> 5V
   - GND -> GND

   Back Sensor:
   - TRIG -> GPIO 7
   - ECHO -> GPIO 8
   - VCC -> 5V
   - GND -> GND

   Bottom Sensor:
   - TRIG -> GPIO 20
   - ECHO -> GPIO 21
   - VCC -> 5V
   - GND -> GND
   ```

2. Power Supply:
   - Connect LM2596S buck converter input to 11.1V battery
   - Adjust output to 5V for Raspberry Pi
   - Connect second buck converter for 12V motor power

### 2. ESP32-CAM Setup
1. Connect components:
   ```
   Programming Connection:
   - 5V -> USB-UART 5V
   - GND -> USB-UART GND
   - U0R -> USB-UART TX
   - U0T -> USB-UART RX
   
   SD Card:
   - Insert microSD card (FAT32 formatted)
   ```

2. Camera positioning:
   - Mount camera in waterproof housing
   - Ensure clear view through housing window

## Software Installation

### 1. Raspberry Pi Software
1. Install OS:
   ```bash
   # Download and flash Raspberry Pi OS Lite to SD card
   # Boot Raspberry Pi and perform initial setup
   ```

2. Enable I2C:
   ```bash
   sudo raspi-config
   # Navigate to Interface Options -> I2C -> Enable
   ```

3. Install repository:
   ```bash
   git clone https://github.com/yourusername/autonomous-underwater-robot.git
   cd autonomous-underwater-robot
   chmod +x setup.sh
   ./setup.sh
   ```

### 2. ESP32-CAM Programming
1. Arduino IDE setup:
   - Install Arduino IDE
   - Add ESP32 board support URL: https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   - Install ESP32 board package
   - Select "AI Thinker ESP32-CAM" board

2. Upload code:
   ```
   - Open esp32-cam/esp32_cam_capture.ino
   - Select correct COM port
   - Upload sketch
   ```

### 3. Web Dashboard Setup
1. Install Node.js and npm
2. Setup dashboard:
   ```bash
   cd web-dashboard
   npm install
   npm start
   ```

## Running the System

1. Start Raspberry Pi services:
   ```bash
   cd rpi
   python app.py
   ```

2. Power up ESP32-CAM:
   - It will automatically start capturing images
   - Check SD card for saved images

3. Access web dashboard:
   - Open browser to http://localhost:3000
   - Use dashboard to control robot

## Testing

1. Test motor control:
   ```bash
   # In Python shell
   from motor_control import MotorControl
   mc = MotorControl()
   mc.forward(50)  # Should move forward at 50% speed
   mc.stop()
   ```

2. Test sensors:
   ```bash
   # In Python shell
   from sensors import MPU6050, UltrasonicSensor
   mpu = MPU6050()
   print(mpu.get_orientation())
   ```

3. Test ESP32-CAM:
   - Check SD card for new images
   - Verify timestamps in filenames

## Troubleshooting

1. Motor Issues:
   - Check voltage at motor terminals
   - Verify GPIO connections
   - Test L298N driver LEDs

2. Sensor Issues:
   - Run i2cdetect for MPU6050
   - Check ultrasonic sensor wiring
   - Verify power supply voltages

3. Communication Issues:
   - Check network connectivity
   - Verify Flask server is running
   - Check web dashboard console for errors

## Safety Checks

1. Before submerging:
   - Verify all seals
   - Check buoyancy
   - Test emergency stop

2. During operation:
   - Monitor battery voltage
   - Watch for unusual behavior
   - Keep safety float ready

3. After use:
   - Dry all components
   - Check for water ingress
   - Recharge battery
