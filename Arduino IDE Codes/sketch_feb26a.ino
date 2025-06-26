// Define flex sensor pins
#define FLEX_SENSOR_1 32
#define FLEX_SENSOR_2 34
#define FLEX_SENSOR_3 35

// Minimum and maximum flex sensor values
#define FLEX_MIN 0
#define FLEX_MAX 4095

// Moving Average Filter parameters
const int NUM_SAMPLES = 10; // Number of samples for moving average
int flexBuffer1[NUM_SAMPLES] = {0};
int flexBuffer2[NUM_SAMPLES] = {0};
int flexBuffer3[NUM_SAMPLES] = {0};
int sampleIndex = 0;

// Exponential Moving Average parameters
const float alpha = 0.2; // Smoothing factor (0.1 - 0.3 recommended)
float ema1 = 0, ema2 = 0, ema3 = 0;

void setup() {
    Serial.begin(115200); // Start serial communication at 115200 baud rate
}

void loop() {
    // Read raw values
    int rawValue1 = analogRead(FLEX_SENSOR_1);
    int rawValue2 = analogRead(FLEX_SENSOR_2);
    int rawValue3 = analogRead(FLEX_SENSOR_3);

    // Map values to normalized range (0-4095)
    int calibratedValue1 = map(rawValue1, FLEX_MIN, FLEX_MAX, 0, 4095);
    int calibratedValue2 = map(rawValue2, FLEX_MIN, FLEX_MAX, 0, 4095);
    int calibratedValue3 = map(rawValue3, FLEX_MIN, FLEX_MAX, 0, 4095);

    // ---- Moving Average Filter ----
    flexBuffer1[sampleIndex] = calibratedValue1;
    flexBuffer2[sampleIndex] = calibratedValue2;
    flexBuffer3[sampleIndex] = calibratedValue3;
    
    sampleIndex = (sampleIndex + 1) % NUM_SAMPLES; // Circular buffer

    int avgValue1 = 0, avgValue2 = 0, avgValue3 = 0;
    for (int i = 0; i < NUM_SAMPLES; i++) {
        avgValue1 += flexBuffer1[i];
        avgValue2 += flexBuffer2[i];
        avgValue3 += flexBuffer3[i];
    }
    avgValue1 /= NUM_SAMPLES;
    avgValue2 /= NUM_SAMPLES;
    avgValue3 /= NUM_SAMPLES;

    // ---- Exponential Moving Average (EMA) Filter ----
    ema1 = alpha * calibratedValue1 + (1 - alpha) * ema1;
    ema2 = alpha * calibratedValue2 + (1 - alpha) * ema2;
    ema3 = alpha * calibratedValue3 + (1 - alpha) * ema3;

    // ---- Choose which filter to use ----
    // Uncomment one of the below lines to use the respective filter

    // Use Moving Average
    int filteredValue1 = avgValue1;
    int filteredValue2 = avgValue2;
    int filteredValue3 = avgValue3;

    // Use Exponential Moving Average (comment out the above three lines to use this)
    // int filteredValue1 = ema1;
    // int filteredValue2 = ema2;
    // int filteredValue3 = ema3;
     int finalValue1;
     int finalValue2;
     int finalValue3;

    // Adjust Flex Sensor 1 and 2 values to match the range of Flex Sensor 3
    if (filteredValue1 >= 3120 && filteredValue1 <= 3122) finalValue1 = 3350;
    if (filteredValue1 >= 3123 && filteredValue1 <= 3125) finalValue1 = 3456;
    if (filteredValue1 >= 3126 && filteredValue1 <= 3128) finalValue1 = 3562;
    if (filteredValue1 >= 3130 && filteredValue1 <= 3132) finalValue1 = 3668;
    if (filteredValue1 >= 3133 && filteredValue1 <= 3135) finalValue1 = 3774;
    if (filteredValue1 >= 3136 && filteredValue1 <= 3138) finalValue1 = 3880;
    if (filteredValue1 >= 3139 && filteredValue1 <= 3141) finalValue1 = 3986;
    if (filteredValue1 >= 3142) finalValue1 = 4095;

    if (filteredValue2 >= 3170 && filteredValue2 <= 3172) finalValue2 = 3350;
    if (filteredValue2 >= 3173 && filteredValue2 <= 3175) finalValue2 = 3456;
    if (filteredValue2 >= 3176 && filteredValue2 <= 3178) finalValue2 = 3562;
    if (filteredValue2 >= 3180 && filteredValue2 <= 3182) finalValue2 = 3668;
    if (filteredValue2 >= 3183 && filteredValue2 <= 3185) finalValue2 = 3774;
    if (filteredValue2 >= 3186 && filteredValue2 <= 3188) finalValue2 = 3880;
    if (filteredValue2 >= 3189 && filteredValue2 <= 3191) finalValue2 = 3986;
    if (filteredValue2 >= 3192) finalValue2 = 4095;

    if (filteredValue3 >= 3520 && filteredValue3 <= 3591) finalValue3 = 3350;
    if (filteredValue3 >= 3592 && filteredValue3 <= 3662) finalValue3 = 3456;
    if (filteredValue3 >= 3663 && filteredValue3 <= 3733) finalValue3 = 3562;
    if (filteredValue3 >= 3734 && filteredValue3 <= 3804) finalValue3 = 3668;
    if (filteredValue3 >= 3805 && filteredValue3 <= 3875) finalValue3 = 3774;
    if (filteredValue3 >= 3756 && filteredValue3 <= 3946) finalValue3 = 3880;
    if (filteredValue3 >= 3947 && filteredValue3 <= 4017) finalValue3 = 3986;
    if (filteredValue3 >= 4018) finalValue3 = 4095;
    // Print filtered values to Serial Monitor
    Serial.print("Flex Sensor 1: ");
    Serial.print(finalValue1);
    Serial.print("\t Flex Sensor 2: ");
    Serial.print(finalValue2);
    Serial.print("\t Flex Sensor 3: ");
    Serial.println(finalValue3);

    delay(100); // Reduce delay for a more responsive filter
}

