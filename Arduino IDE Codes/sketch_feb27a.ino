#include <Wire.h>
#include <math.h>

#define SDA_PIN 21
#define SCL_PIN 22

#define MPU1_ADDR 0x68
#define MPU2_ADDR 0x69

// Flex Sensor Pins
#define FLEX_PIN_1 32
#define FLEX_PIN_2 34
#define FLEX_PIN_3 35

const float GYRO_SENSITIVITY = 131.0; // LSB/°/s
float angleX_1 = 0, angleY_1 = 0, angleZ_1 = 0;
float angleX_2 = 0, angleY_2 = 0, angleZ_2 = 0;

float pitch_1 = 0, roll_1 = 0, yaw_1 = 0;
float pitch_2 = 0, roll_2 = 0, yaw_2 = 0;

float alpha = 0.98;  // Complementary filter constant

unsigned long lastTime = 0;
bool mpu1_found = false;
bool mpu2_found = false;

void setup() {
  Serial.begin(115200);
  Wire.begin(SDA_PIN, SCL_PIN);

  Serial.println("\n🔍 Scanning I2C devices...");
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.print("✅ I2C device found at 0x");
      Serial.println(addr, HEX);
      if (addr == MPU1_ADDR) mpu1_found = true;
      if (addr == MPU2_ADDR) mpu2_found = true;
    }
  }

  if (!mpu1_found && !mpu2_found) {
    Serial.println("❌ No MPU6050 found! Check wiring.");
    while (1);
  }

  if (mpu1_found) initMPU6050(MPU1_ADDR);
  if (mpu2_found) initMPU6050(MPU2_ADDR);

  lastTime = millis();
}

void loop() {
  // --- [FILTER] Low-pass filter applied to flex sensor readings ---
  static float filteredADC1 = 0, filteredADC2 = 0, filteredADC3 = 0;
  float alphaFlex = 0.1;

  filteredADC1 = alphaFlex * analogRead(FLEX_PIN_1) + (1 - alphaFlex) * filteredADC1;
  filteredADC2 = alphaFlex * analogRead(FLEX_PIN_2) + (1 - alphaFlex) * filteredADC2;
  filteredADC3 = alphaFlex * analogRead(FLEX_PIN_3) + (1 - alphaFlex) * filteredADC3;

  // --- [CALIBRATION] ADC to Angle mapping for Flex Sensors ---
  int angle1 = getAngleFlex1((int)filteredADC1);
  int angle2 = getAngleFlex2((int)filteredADC2);
  int angle3 = getAngleFlex3((int)filteredADC3);

  Serial.print("🎛️ Flex1: ADC = "); Serial.print((int)filteredADC1); Serial.print(" | Angle: "); Serial.print(angle1); Serial.println("°");
  Serial.print("🎛️ Flex2: ADC = "); Serial.print((int)filteredADC2); Serial.print(" | Angle: "); Serial.print(angle2); Serial.println("°");
  Serial.print("🎛️ Flex3: ADC = "); Serial.print((int)filteredADC3); Serial.print(" | Angle: "); Serial.print(angle3); Serial.println("°");
  Serial.println("------------------------------------------------");

  if (mpu1_found) readMPU6050(MPU1_ADDR, angleX_1, angleY_1, angleZ_1, pitch_1, roll_1, yaw_1);
  if (mpu2_found) readMPU6050(MPU2_ADDR, angleX_2, angleY_2, angleZ_2, pitch_2, roll_2, yaw_2);

  delay(1000);
}

void initMPU6050(int address) {
  Wire.beginTransmission(address);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission();
}

// --- [FILTER] Complementary filter applied to MPU6050 orientation ---
void readMPU6050(int address, float &angleX, float &angleY, float &angleZ, float &pitch, float &roll, float &yaw) {
  Wire.beginTransmission(address);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(address, 14, true);

  if (Wire.available() < 14) {
    Serial.print("⚠️ MPU6050 at 0x");
    Serial.print(address, HEX);
    Serial.println(" is not responding!");
    return;
  }

  int16_t AccX = Wire.read() << 8 | Wire.read();
  int16_t AccY = Wire.read() << 8 | Wire.read();
  int16_t AccZ = Wire.read() << 8 | Wire.read();
  Wire.read(); Wire.read(); // Skip temperature
  int16_t GyroX = Wire.read() << 8 | Wire.read();
  int16_t GyroY = Wire.read() << 8 | Wire.read();
  int16_t GyroZ = Wire.read() << 8 | Wire.read();

  unsigned long currentTime = millis();
  float dt = (currentTime - lastTime) / 1000.0;

  float gyroX_dps = GyroX / GYRO_SENSITIVITY;
  float gyroY_dps = GyroY / GYRO_SENSITIVITY;
  float gyroZ_dps = GyroZ / GYRO_SENSITIVITY;

  angleX += gyroX_dps * dt;
  angleY += gyroY_dps * dt;
  angleZ += gyroZ_dps * dt;

  // Accelerometer-based pitch and roll
  float accPitch = atan2(AccY, sqrt(AccX * AccX + AccZ * AccZ)) * 180 / PI;
  float accRoll  = atan2(-AccX, AccZ) * 180 / PI;

  // Complementary filter fusion
  pitch = alpha * (pitch + gyroY_dps * dt) + (1 - alpha) * accPitch;
  roll  = alpha * (roll  + gyroX_dps * dt) + (1 - alpha) * accRoll;
  yaw   += gyroZ_dps * dt;  // Yaw can't be corrected by accel, so integrate gyro

  Serial.print("🎯 MPU6050 at 0x"); Serial.print(address, HEX);
  Serial.print(" | Pitch: "); Serial.print(pitch, 2);
  Serial.print(" | Roll: "); Serial.print(roll, 2);
  Serial.print(" | Yaw: "); Serial.println(yaw, 2);

  lastTime = currentTime;
}

// --- [CALIBRATION] ADC to Angle mapping for Flex Sensors ---
int getAngleFlex1(int adc) {
  if (adc <= 3350) return 0;
  else if (adc <= 3456) return 15;
  else if (adc <= 3562) return 30;
  else if (adc <= 3668) return 45;
  else if (adc <= 3774) return 60;
  else if (adc <= 3880) return 75;
  else return 90;
}

int getAngleFlex2(int adc) {
  return getAngleFlex1(adc); // Same mapping as Flex1
}

int getAngleFlex3(int adc) {
  return getAngleFlex1(adc); // Same mapping as Flex1
}
