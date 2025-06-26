import serial
import csv
import time
import threading
import tkinter as tk
from tkinter import messagebox
import os

SERIAL_PORT = "COM9"  # Update this if needed
BAUD_RATE = 115200

timestamp_now = time.strftime("%Y-%m-%d_%H-%M-%S")
OUTPUT_DIR = "C:/Mini Project/"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"grip_data_{timestamp_now}.csv")

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)

logging_active = True
running = True
gesture_name = ""
object_used = ""

def read_serial_data():
    global logging_active, running, gesture_name, object_used

    with open(OUTPUT_FILE, "w", newline="") as file:
        writer = csv.writer(file)

        # ✅ Updated headers for new serial format
        writer.writerow(["Timestamp", "Flex1_ADC", "Flex1_Angle",
                         "Flex2_ADC", "Flex2_Angle", "Flex3_ADC", "Flex3_Angle",
                         "MPU1_Pitch", "MPU1_Roll", "MPU1_Yaw",
                         "MPU2_Pitch", "MPU2_Roll", "MPU2_Yaw",
                         "Gesture_Name", "Object_Used"])

        print(f"📡 Logging data to {OUTPUT_FILE}")

        # Default values
        flex1_adc = flex1_angle = flex2_adc = flex2_angle = flex3_adc = flex3_angle = 0
        mpu1_pitch = mpu1_roll = mpu1_yaw = 0
        mpu2_pitch = mpu2_roll = mpu2_yaw = 0

        try:
            while running:
                line = ser.readline().decode("utf-8").strip()

                if line:
                    print(line)

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
                        elif "MPU6050 at 0x68" in line:
                            parts = line.split(" | ")
                            mpu1_pitch = float(parts[1].split(": ")[1])
                            mpu1_roll = float(parts[2].split(": ")[1])
                            mpu1_yaw = float(parts[3].split(": ")[1])
                        elif "MPU6050 at 0x69" in line:
                            parts = line.split(" | ")
                            mpu2_pitch = float(parts[1].split(": ")[1])
                            mpu2_roll = float(parts[2].split(": ")[1])
                            mpu2_yaw = float(parts[3].split(": ")[1])

                        if logging_active:
                            writer.writerow([
                                time.strftime("%Y-%m-%d %H:%M:%S"),
                                flex1_adc, flex1_angle,
                                flex2_adc, flex2_angle,
                                flex3_adc, flex3_angle,
                                mpu1_pitch, mpu1_roll, mpu1_yaw,
                                mpu2_pitch, mpu2_roll, mpu2_yaw,
                                gesture_name, object_used
                            ])
                            file.flush()

                    except Exception as e:
                        print(f"⚠️ Error processing line: {e}")
        finally:
            ser.close()

def pause_logging():
    global logging_active, gesture_name, object_used
    gesture_name = gesture_entry.get() or "No Gesture"
    object_used = object_entry.get() or "No Object"
    logging_active = False
    status_label.config(text="Status: Paused")
    gesture_label.config(text=f"Gesture: {gesture_name}")
    object_label.config(text=f"Object: {object_used}")

def resume_logging():
    global logging_active
    logging_active = True
    status_label.config(text="Status: Logging")

def stop_program():
    global running
    running = False
    ser.close()
    root.quit()
    messagebox.showinfo("Data Logging", f"✅ Data saved to:\n{OUTPUT_FILE}")

# GUI Setup
root = tk.Tk()
root.title("ESP32 Grip Data Logger")
root.geometry("400x400")

status_label = tk.Label(root, text="Status: Logging", font=("Arial", 14))
status_label.pack(pady=10)

gesture_label = tk.Label(root, text="Gesture: Not Set", font=("Arial", 12))
gesture_label.pack()

object_label = tk.Label(root, text="Object: Not Set", font=("Arial", 12))
object_label.pack()

gesture_entry = tk.Entry(root, font=("Arial", 12), width=30)
gesture_entry.pack(pady=10)
gesture_entry.insert(0, "Enter Gesture")

object_entry = tk.Entry(root, font=("Arial", 12), width=30)
object_entry.pack(pady=10)
object_entry.insert(0, "Enter Object")

pause_button = tk.Button(root, text="Pause Logging", command=pause_logging, font=("Arial", 12), width=20)
pause_button.pack(pady=5)

resume_button = tk.Button(root, text="Resume Logging", command=resume_logging, font=("Arial", 12), width=20)
resume_button.pack(pady=5)

stop_button = tk.Button(root, text="Stop & Save", command=stop_program, font=("Arial", 12), width=20, bg="red", fg="white")
stop_button.pack(pady=10)

# Start thread
serial_thread = threading.Thread(target=read_serial_data, daemon=True)
serial_thread.start()

root.mainloop()
