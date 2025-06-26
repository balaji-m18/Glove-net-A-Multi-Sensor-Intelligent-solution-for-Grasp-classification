import serial
import csv
import re
from datetime import datetime
import threading
import queue
import tkinter as tk
from tkinter import messagebox

# Settings
SERIAL_PORT = 'COM9'
BAUD_RATE = 115200
filename = "C:/Mini Project/mpu_orientation_log.csv"

# Flags and Data
logging_active = True
running = True
phase = ""
grip_type = ""
object_name = ""

# Queues
data_queue = queue.Queue()

# Serial Setup
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
ser.flush()

# GUI callbacks
def pause_logging():
    global logging_active
    logging_active = False
    status_label.config(text="Status: Paused")

def resume_logging():
    global logging_active, phase, grip_type, object_name
    phase = phase_entry.get()
    grip_type = grip_type_entry.get()
    object_name = object_entry.get()
    logging_active = True
    status_label.config(text="Status: Logging Data")

def stop_program():
    global running
    running = False
    ser.close()
    root.quit()
    messagebox.showinfo("Logging Stopped", f"Data saved to {filename}")

# Serial reader thread
def read_serial():
    while running:
        try:
            line = ser.readline().decode('utf-8').strip()
            match = re.search(r'MPU6050 at 0x(..) \| Pitch: ([\d\.\-]+) \| Roll: ([\d\.\-]+) \| Yaw: ([\d\.\-]+)', line)
            if match and match.group(1) == '69':
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                pitch = float(match.group(2))
                roll = float(match.group(3))
                yaw = float(match.group(4))
                if logging_active:
                    data_queue.put([timestamp, pitch, roll, yaw, phase, grip_type, object_name])
        except Exception as e:
            pass  # Silently skip bad lines

# CSV writer thread
def write_csv():
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "MPU2_Pitch", "MPU2_Roll", "MPU2_Yaw", "Phase", "Grip_Type", "Object"])
        while running or not data_queue.empty():
            try:
                row = data_queue.get(timeout=1)
                writer.writerow(row)
            except queue.Empty:
                continue

# GUI setup
root = tk.Tk()
root.title("MPU Logger GUI")
root.geometry("400x400")

status_label = tk.Label(root, text="Status: Logging Data", font=("Arial", 12))
status_label.pack(pady=10)

pause_btn = tk.Button(root, text="Pause", command=pause_logging, width=20)
pause_btn.pack(pady=5)

resume_btn = tk.Button(root, text="Resume", command=resume_logging, width=20)
resume_btn.pack(pady=5)

stop_btn = tk.Button(root, text="Stop and Save", command=stop_program, width=20, bg="red", fg="white")
stop_btn.pack(pady=5)

tk.Label(root, text="Phase:").pack()
phase_entry = tk.Entry(root)
phase_entry.pack(pady=2)

tk.Label(root, text="Grip Type:").pack()
grip_type_entry = tk.Entry(root)
grip_type_entry.pack(pady=2)

tk.Label(root, text="Object:").pack()
object_entry = tk.Entry(root)
object_entry.pack(pady=2)

# Start threads
threading.Thread(target=read_serial, daemon=True).start()
threading.Thread(target=write_csv, daemon=True).start()

# Run GUI
root.mainloop()
