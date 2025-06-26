import serial
import csv
import time
import threading
import tkinter as tk
from tkinter import messagebox
import os

# Configure the serial connection
SERIAL_PORT = "COM9"  # Update as per your system
BAUD_RATE = 115200

# Create a unique filename for each session
timestamp_now = time.strftime("%Y-%m-%d_%H-%M-%S")
OUTPUT_DIR = "C:/Mini Project/"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"arduino_data_{timestamp_now}.csv")

# Open serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # Allow time for ESP32 to initialize

# Flags for controlling data logging
logging_active = True
running = True  
gesture_name = ""  
object_used = ""  

# Function to process incoming serial data
def read_serial_data():
    global logging_active, running, gesture_name, object_used

    with open(OUTPUT_FILE, "w", newline="") as file:
        writer = csv.writer(file)

        # Write header (Added "Object Used")
        writer.writerow(["Timestamp", "Upload_Timestamp", "Flex1_ADC", "Flex1_Angle",
                         "Flex2_ADC", "Flex2_Angle", "Flex3_ADC", "Flex3_Angle",
                         "MPU1_GyroX", "MPU1_GyroY", "MPU1_GyroZ", "MPU1_AngleX", "MPU1_AngleY", "MPU1_AngleZ",
                         "MPU2_GyroX", "MPU2_GyroY", "MPU2_GyroZ", "MPU2_AngleX", "MPU2_AngleY", "MPU2_AngleZ",
                         "Gesture_Name", "Object_Used"])

        print(f"📡 Logging data to {OUTPUT_FILE}")

        # Default values for MPU data
        flex1_adc = flex1_angle = flex2_adc = flex2_angle = flex3_adc = flex3_angle = 0
        mpu1_gyroX = mpu1_gyroY = mpu1_gyroZ = mpu1_angleX = mpu1_angleY = mpu1_angleZ = 0
        mpu2_gyroX = mpu2_gyroY = mpu2_gyroZ = mpu2_angleX = mpu2_angleY = mpu2_angleZ = 0

        try:
            while running:
                line = ser.readline().decode("utf-8").strip()

                if line:
                    print(line)  

                    if line == "STOP":
                        print("\n🚪 Stop command received. Stopping data collection.")
                        break

                    try:
                        if "Flex1:" in line:
                            flex1_adc = int(line.split("ADC = ")[1].split(" | ")[0])
                            flex1_angle = int(line.split("Angle: ")[1].split("°")[0])
                        elif "Flex2:" in line:
                            flex2_adc = int(line.split("ADC = ")[1].split(" | ")[0])
                            flex2_angle = int(line.split("Angle: ")[1].split("°")[0])
                        elif "Flex3:" in line:
                            flex3_adc = int(line.split("ADC = ")[1].split(" | ")[0])
                            flex3_angle = int(line.split("Angle: ")[1].split("°")[0])
                        elif "MPU6050 at 0x68" in line:  # MPU1 Data
                            data = [float(x.split(": ")[1]) for x in line.split(" | ")[1:]]
                            if len(data) == 6:  # Ensure valid data
                                mpu1_gyroX, mpu1_gyroY, mpu1_gyroZ, mpu1_angleX, mpu1_angleY, mpu1_angleZ = data
                            else:
                                print("⚠️ Invalid MPU1 data, using last known values.")
                        elif "MPU6050 at 0x69" in line:  # MPU2 Data
                            data = [float(x.split(": ")[1]) for x in line.split(" | ")[1:]]
                            if len(data) == 6:  # Ensure valid data
                                mpu2_gyroX, mpu2_gyroY, mpu2_gyroZ, mpu2_angleX, mpu2_angleY, mpu2_angleZ = data
                            else:
                                print("⚠️ Invalid MPU2 data, using last known values.")

                        # Record timestamps
                        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                        upload_timestamp = time.strftime("%H:%M:%S")

                        # Write to CSV if logging is active
                        if logging_active:
                            writer.writerow([timestamp, upload_timestamp, flex1_adc, flex1_angle, flex2_adc, flex2_angle, flex3_adc, flex3_angle,
                                             mpu1_gyroX, mpu1_gyroY, mpu1_gyroZ, mpu1_angleX, mpu1_angleY, mpu1_angleZ,
                                             mpu2_gyroX, mpu2_gyroY, mpu2_gyroZ, mpu2_angleX, mpu2_angleY, mpu2_angleZ, 
                                             gesture_name, object_used])
                            file.flush()

                    except Exception as e:
                        print(f"⚠️ Error processing line: {e}. Using default values.")

        except KeyboardInterrupt:
            print("\n🚪 Stopping data collection.")
        finally:
            ser.close()

# GUI Functions
def pause_logging():
    global logging_active, gesture_name, object_used

    # Store values from text entries
    gesture_name = gesture_entry.get() or "No Gesture"
    object_used = object_entry.get() or "No Object"

    logging_active = False
    status_label.config(text="Status: Paused")
    gesture_label.config(text=f"Gesture: {gesture_name}")
    object_label.config(text=f"Object: {object_used}")

def resume_logging():
    global logging_active
    logging_active = True
    status_label.config(text="Status: Logging Data")

def stop_program():
    global running
    running = False
    ser.close()
    root.quit()
    messagebox.showinfo("Data Logging", f"Data logging stopped and saved in:\n{OUTPUT_FILE}")

# Create GUI window
root = tk.Tk()
root.title("ESP32 Data Logger")
root.geometry("400x400")

status_label = tk.Label(root, text="Status: Logging Data", font=("Arial", 14))
status_label.pack(pady=20)

gesture_label = tk.Label(root, text="Gesture: Not Set", font=("Arial", 12))
gesture_label.pack(pady=5)

object_label = tk.Label(root, text="Object: Not Set", font=("Arial", 12))
object_label.pack(pady=5)

# Create text entries for gesture name and object used
gesture_entry = tk.Entry(root, font=("Arial", 12), width=30)
gesture_entry.pack(pady=10)

object_entry = tk.Entry(root, font=("Arial", 12), width=30)
object_entry.pack(pady=10)

# Create buttons
pause_button = tk.Button(root, text="Pause Logging", command=pause_logging, font=("Arial", 12), width=20)
pause_button.pack(pady=5)

resume_button = tk.Button(root, text="Resume Logging", command=resume_logging, font=("Arial", 12), width=20)
resume_button.pack(pady=5)

stop_button = tk.Button(root, text="Stop & Save", command=stop_program, font=("Arial", 12), width=20, bg="red", fg="white")
stop_button.pack(pady=5)

# Run serial reading in a separate thread
serial_thread = threading.Thread(target=read_serial_data, daemon=True)
serial_thread.start()

# Start GUI
root.mainloop()
