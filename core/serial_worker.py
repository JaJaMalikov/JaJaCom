### Fichier : core/serial_worker.py

from PySide6.QtCore import QObject, Signal, QThread
import serial
import threading

class SerialWorker(QObject):
    line_received = Signal(str)

    def __init__(self):
        super().__init__()
        self.ser = None
        self.thread = None
        self.running = False

    def connect(self, port, baudrate):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=0.1)
            self.running = True
            self.thread = threading.Thread(target=self.read_loop, daemon=True)
            self.thread.start()
            return True
        except Exception as e:
            self.line_received.emit(f"[Erreur connexion] {e}")
            return False

    def disconnect(self):
        self.running = False
        if self.ser:
            try:
                if self.ser.is_open:
                    self.ser.close()
            except Exception as e:
                self.line_received.emit(f"[Erreur fermeture] {e}")
            finally:
                self.ser = None

    def is_connected(self):
        return self.ser is not None and self.ser.is_open

    def read_loop(self):
        while self.running and self.ser:
            try:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode('utf-8', errors='replace').strip()
                    self.line_received.emit(line)
            except Exception as e:
                self.line_received.emit(f"[Erreur lecture] {e}")
                self.disconnect()
                break

    def send_line(self, text):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write((text + '\n').encode('utf-8'))
            except Exception as e:
                self.line_received.emit(f"[Erreur écriture] {e}")
