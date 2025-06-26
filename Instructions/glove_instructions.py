import tkinter as tk
from tkinter import ttk
import serial
import threading
import queue

SERIAL_PORT = 'COM9'  # Update if different
BAUDRATE = 115200

# Thread-safe queue for serial data
serial_queue = queue.Queue()

class TherapyMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Therapy Monitor")
        
        # Serial connection
        self.ser = None
        self.connect_serial()
        
        # GUI variables
        self.phase_var = tk.StringVar(value="Waiting...")
        self.countdown_var = tk.StringVar(value="0")
        
        # Setup UI
        self.create_widgets()
        
        # Start serial thread if connected
        if self.ser and self.ser.is_open:
            self.serial_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.serial_thread.start()
            self.root.after(100, self.process_queue)

    def connect_serial(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
            print(f"Connected to {SERIAL_PORT}")
        except serial.SerialException as e:
            print(f"Connection error: {e}")

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status display
        ttk.Label(main_frame, text="Current Phase:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(main_frame, textvariable=self.phase_var, font=('Arial', 12, 'bold')).grid(row=0, column=1, sticky="w")
        
        ttk.Label(main_frame, text="Countdown:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Label(main_frame, textvariable=self.countdown_var, font=('Arial', 12, 'bold')).grid(row=1, column=1, sticky="w")
        
        # Control buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Start", command=self.send_start).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Pause", command=self.send_pause).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Resume", command=self.send_resume).grid(row=0, column=2, padx=5)

    def read_serial(self):
        """Background thread for reading serial data"""
        while self.ser and self.ser.is_open:
            try:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    serial_queue.put(line)
            except Exception as e:
                print(f"Serial error: {str(e)}")
                break

    def process_queue(self):
        """Process messages from serial queue"""
        while not serial_queue.empty():
            line = serial_queue.get()
            self.parse_serial_data(line)
        self.root.after(100, self.process_queue)

    def parse_serial_data(self, line):
        """Parse and display serial data"""
        if "Phase:" in line and "Countdown:" in line:
            try:
                # Split into components
                phase_part, countdown_part = line.split("|")[:2]
                
                # Extract values
                phase = phase_part.split(":")[1].strip()
                countdown = countdown_part.split(":")[1].strip()
                
                # Update GUI
                self.phase_var.set(phase)
                self.countdown_var.set(countdown)
            except Exception as e:
                print(f"Parse error: {str(e)}")
        # Else: ignore lines that don't match

    def send_command(self, cmd):
        """Send command to ESP32"""
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(f"{cmd}\n".encode())
            except Exception as e:
                print(f"Command error: {str(e)}")

    def send_start(self):
        self.send_command("start")

    def send_pause(self):
        self.send_command("pause")

    def send_resume(self):
        self.send_command("resume")

    def on_close(self):
        """Cleanup on window close"""
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TherapyMonitor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
