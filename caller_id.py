import serial
import tkinter as tk
from tkinter import ttk
import threading
import time

class CallerIDApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Arayan Numara Gösterimi")
        self.root.geometry("400x300")
        
        # Ana frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Başlık
        self.title_label = ttk.Label(self.main_frame, text="Arayan Numara", font=("Helvetica", 16, "bold"))
        self.title_label.grid(row=0, column=0, pady=10)
        
        # Numara gösterimi için label
        self.number_label = ttk.Label(self.main_frame, text="", font=("Helvetica", 24))
        self.number_label.grid(row=1, column=0, pady=20)
        
        # Seri port ayarları
        self.serial_port = None
        self.is_running = True
        
        # Seri port bağlantısını başlat
        self.start_serial_thread()
    
    def start_serial_thread(self):
        try:
            self.serial_port = serial.Serial(
                port='/dev/ttyUSB0',  # Port adını sisteminize göre değiştirin
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            
            # Seri port okuma thread'ini başlat
            self.serial_thread = threading.Thread(target=self.read_serial)
            self.serial_thread.daemon = True
            self.serial_thread.start()
            
        except serial.SerialException as e:
            self.number_label.config(text=f"Bağlantı Hatası: {str(e)}")
    
    def read_serial(self):
        while self.is_running:
            try:
                if self.serial_port and self.serial_port.is_open:
                    data = self.serial_port.readline().decode('utf-8').strip()
                    if data:
                        # Gelen veriyi ekranda göster
                        self.root.after(0, self.update_number, data)
            except Exception as e:
                print(f"Okuma hatası: {str(e)}")
            time.sleep(0.1)
    
    def update_number(self, number):
        self.number_label.config(text=number)
    
    def on_closing(self):
        self.is_running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CallerIDApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop() 