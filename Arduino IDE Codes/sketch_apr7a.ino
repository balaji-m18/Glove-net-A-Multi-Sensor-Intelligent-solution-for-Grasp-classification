#include <Wire.h>

#define SDA_PIN 21  // ESP32 I2C SDA pin
#define SCL_PIN 22  // ESP32 I2C SCL pin

#define MPU1_ADDR 0x68  // First MPU6050 (AD0 = GND)
#define MPU2_ADDR 0x69  // Second MPU6050 (AD0 = VCC)

// Flex Sensor Pins
#define FLEX_PIN_1 32
#define FLEX_PIN_2 34
#define FLEX_PIN_3 35

// Gyroscope Sensitivity for ±250°/s
const float GYRO_SENSITIVITY = 131.0;  // (LSB/°/s)

float angleX_1 = 0, angleY_1 = 0, angleZ_1 = 0;
float angleX_2 = 0, angleY_2 = 0, angleZ_2 = 0;

unsigned long lastTime = 0;
bool mpu1_found = false;
bool mpu2_found = false;

// Rolling buffer for moving average (last 5 samples)
const int N = 5;
float gyroX_buffer[N] = {0}, gyroY_buffer[N] = {0}, gyroZ_buffer[N] = {0};
int bufferIndex = 0;

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
        while (1);  // Stop execution if no sensors are detected
    }

    // Initialize MPU6050
    if (mpu1_found) initMPU6050(MPU1_ADDR);
    if (mpu2_found) initMPU6050(MPU2_ADDR);

    lastTime = millis();
}

void loop() {
    // Read and print flex sensor data
    int flex1_adc = analogRead(FLEX_PIN_1);
    int flex2_adc = analogRead(FLEX_PIN_2);
    int flex3_adc = analogRead(FLEX_PIN_3);

    int angle1 = getAngleFlex1(flex1_adc);
    int angle2 = getAngleFlex2(flex2_adc);
    int angle3 = getAngleFlex3(flex3_adc);

    Serial.print("🎛️ Flex1: ADC = "); Serial.print(flex1_adc); Serial.print(" | Angle: "); Serial.print(angle1); Serial.println("°");
    Serial.print("🎛️ Flex2: ADC = "); Serial.print(flex2_adc); Serial.print(" | Angle: "); Serial.print(angle2); Serial.println("°");
    Serial.print("🎛️ Flex3: ADC = "); Serial.print(flex3_adc); Serial.print(" | Angle: "); Serial.print(angle3); Serial.println("°");

    Serial.println("------------------------------------------------");

    // Read and print MPU6050 data
    if (mpu1_found) readMPU6050(MPU1_ADDR, angleX_1, angleY_1, angleZ_1);
    if (mpu2_found) readMPU6050(MPU2_ADDR, angleX_2, angleY_2, angleZ_2);

    delay(1000);  // Wait 1 second before next reading
}

// Function to initialize MPU6050
void initMPU6050(int address) {
    Wire.beginTransmission(address);
    Wire.write(0x6B);  // Power Management 1 register
    Wire.write(0);  // Wake up MPU6050
    Wire.endTransmission();
}

// Function to apply simple low-pass filter
float lowPassFilter(float input, float prev, float alpha) {
    return alpha * input + (1 - alpha) * prev;
}

// Function to compute moving average
float computeMovingAverage(float buffer[]) {
    float sum = 0;
    for (int i = 0; i < N; i++) sum += buffer[i];
    return sum / N;
}

// Function to read data from MPU6050
void readMPU6050(int address, float &angleX, float &angleY, float &angleZ) {
    Wire.beginTransmission(address);
    Wire.write(0x3B);  // Start reading from ACCEL_XOUT_H
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
    Wire.read(); Wire.read();  // Skip temperature
    int16_t GyroX = Wire.read() << 8 | Wire.read();
    int16_t GyroY = Wire.read() << 8 | Wire.read();
    int16_t GyroZ = Wire.read() << 8 | Wire.read();

    unsigned long currentTime = millis();
    float dt = (currentTime - lastTime) / 1000.0;

    // Convert raw to degrees/sec
    float gyroX_dps = GyroX / GYRO_SENSITIVITY;
    float gyroY_dps = GyroY / GYRO_SENSITIVITY;
    float gyroZ_dps = GyroZ / GYRO_SENSITIVITY;

    // Apply low-pass filter (alpha = 0.5 for smoothing)
    static float prevX = 0, prevY = 0, prevZ = 0;
    gyroX_dps = lowPassFilter(gyroX_dps, prevX, 0.5);
    gyroY_dps = lowPassFilter(gyroY_dps, prevY, 0.5);
    gyroZ_dps = lowPassFilter(gyroZ_dps, prevZ, 0.5);

    prevX = gyroX_dps;
    prevY = gyroY_dps;
    prevZ = gyroZ_dps;

    // Add to rolling buffer for moving average
    gyroX_buffer[bufferIndex] = gyroX_dps;
    gyroY_buffer[bufferIndex] = gyroY_dps;
    gyroZ_buffer[bufferIndex] = gyroZ_dps;
    bufferIndex = (bufferIndex + 1) % N;

    float avgX = computeMovingAverage(gyroX_buffer);
    float avgY = computeMovingAverage(gyroY_buffer);
    float avgZ = computeMovingAverage(gyroZ_buffer);

    // Integrate average angular velocity to get angle
    angleX += avgX * dt;
    angleY += avgY * dt;
    angleZ += avgZ * dt;

    Serial.print("🎯 MPU6050 at 0x");
    Serial.print(address, HEX);
    Serial.print(" | GyroX: "); Serial.print(avgX);
    Serial.print(" | GyroY: "); Serial.print(avgY);
    Serial.print(" | GyroZ: "); Serial.print(avgZ);
    Serial.print(" | AngleX: "); Serial.print(angleX);
    Serial.print(" | AngleY: "); Serial.print(angleY);
    Serial.print(" | AngleZ: "); Serial.println(angleZ);

    lastTime = currentTime;
}

// Flex Sensor Calibration Functions
int getAngleFlex1(int adc) {
    if (adc >= 0 && adc <= 3350) return 0;
    else if (adc >= 3351 && adc <= 3456) return 15;
    else if (adc >= 3457 && adc <= 3562) return 30;
    else if (adc >= 3563 && adc <= 3668) return 45;
    else if (adc >= 3669 && adc <= 3774) return 60;
    else if (adc >= 3775 && adc <= 3880) return 75;
    else if (adc >= 3881 && adc <= 4095) return 90;
    else return 90;
}

int getAngleFlex2(int adc) {
    if (adc >= 0 && adc <= 3350) return 0;
    else if (adc >= 3351 && adc <= 3456) return 15;
    else if (adc >= 3457 && adc <= 3562) return 30;
    else if (adc >= 3563 && adc <= 3668) return 45;
    else if (adc >= 3669 && adc <= 3774) return 60;
    else if (adc >= 3775 && adc <= 3880) return 75;
    else if (adc >= 3881 && adc <= 4095) return 90;
    else return 90;
}

int getAngleFlex3(int adc) {
    if (adc >= 0 && adc <= 3350) return 0;
    else if (adc >= 3351 && adc <= 3456) return 15;
    else if (adc >= 3457 && adc <= 3562) return 30;
    else if (adc >= 3563 && adc <= 3668) return 45;
    else if (adc >= 3669 && adc <= 3774) return 60;
    else if (adc >= 3775 && adc <= 3880) return 75;
    else if (adc >= 3881 && adc <= 4095) return 90;
    else return 90;
}

