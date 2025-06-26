#include <Wire.h>
#include <math.h>

#define SDA_PIN 21
#define SCL_PIN 22

#define MPU2_ADDR 0x69

const float GYRO_SENSITIVITY = 131.0; // LSB/°/s

float angleX_2 = 0, angleY_2 = 0, angleZ_2 = 0;
float pitch_2 = 0, roll_2 = 0, yaw_2 = 0;
float prevPitch = 0;

float alpha = 0.98;  // Complementary filter constant
unsigned long lastTime = 0;
bool mpu2_found = false;

// Format millis() to HH:MM:SS
String getFormattedTime(unsigned long ms) {
  unsigned long seconds = ms / 1000;
  unsigned int hours = seconds / 3600;
  unsigned int minutes = (seconds % 3600) / 60;
  unsigned int secs = seconds % 60;

  char buf[10];
  sprintf(buf, "%02u:%02u:%02u", hours, minutes, secs);
  return String(buf);
}

// Phase detection using ONLY deltaPitch
String detectPhase(float deltaPitch) {
  if (deltaPitch >= 15.51 && deltaPitch <= 15.81) {
    return "Holding";
  } else if (deltaPitch >= 5.70 && deltaPitch <= 14.66) {
    return "Moving Down";
  } else if (deltaPitch >= 7.04 && deltaPitch <= 9.73) {
    return "Moving Left";
  } else if (deltaPitch >= 4.30 && deltaPitch <= 19.86) {
    return "Moving Up";
  } else if (deltaPitch >= -12.57 && deltaPitch <= 12.36) {
    return "Reaching";
  } else if (deltaPitch >= -0.58 && deltaPitch <= 0.10) {
    return "Relaxing";
  } else if (deltaPitch >= -9.16 && deltaPitch <= 14.44) {
    return "Releasing";
  }

  return "Unknown Phase";
}

void setup() {
  Serial.begin(115200);
  Wire.begin(SDA_PIN, SCL_PIN);

  Serial.println("\n🔍 Scanning I2C devices...");
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.print("✅ I2C device found at 0x");
      Serial.println(addr, HEX);
      if (addr == MPU2_ADDR) mpu2_found = true;
    }
  }

  if (!mpu2_found) {
    Serial.println("❌ MPU6050 at 0x69 not found! Check wiring.");
    while (1);
  }

  initMPU6050(MPU2_ADDR);
  lastTime = millis();
}

void loop() {
  if (mpu2_found) {
    readMPU6050(MPU2_ADDR, angleX_2, angleY_2, angleZ_2, pitch_2, roll_2, yaw_2);

    float deltaPitch = pitch_2 - prevPitch;
    String phase = detectPhase(deltaPitch);

    Serial.print("🧠 Detected Phase (ΔPitch): ");
    Serial.println(phase);

    prevPitch = pitch_2;
  }

  delay(1000); // Sampling rate
}

void initMPU6050(int address) {
  Wire.beginTransmission(address);
  Wire.write(0x6B);  // Power management register
  Wire.write(0);     // Wake up the MPU6050
  Wire.endTransmission();
}

void readMPU6050(int address, float &angleX, float &angleY, float &angleZ, float &pitch, float &roll, float &yaw) {
  Wire.beginTransmission(address);
  Wire.write(0x3B); // Start reading at ACCEL_XOUT_H
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

  float accPitch = atan2(AccY, sqrt(AccX * AccX + AccZ * AccZ)) * 180 / PI;
  float accRoll  = atan2(-AccX, AccZ) * 180 / PI;

  pitch = alpha * (pitch + gyroY_dps * dt) + (1 - alpha) * accPitch;
  roll  = alpha * (roll  + gyroX_dps * dt) + (1 - alpha) * accRoll;
  yaw   += gyroZ_dps * dt;

  Serial.print("⏱️ "); Serial.print(getFormattedTime(currentTime));
  Serial.print(" | Pitch: "); Serial.print(pitch, 2);
  Serial.print(" | ΔPitch: "); Serial.println(pitch - prevPitch, 2);

  lastTime = currentTime;
}
