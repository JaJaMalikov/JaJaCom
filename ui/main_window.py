### Fichier : ui/main_window.py

from PySide6.QtWidgets import (
    QWidget, QMainWindow, QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QLineEdit, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from core.serial_worker import SerialWorker
import serial.tools.list_ports
from ui.custom_widgets import RefreshableComboBox
from datetime import datetime  # tout en haut du fichier si pas déjà fait


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JaJaCom GUI")
        self.resize(800, 600)
        self.connected = False

        # --- Widgets principaux ---
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("background-color: #111; color: #eee; font-family: monospace;")

        self.port_combo = RefreshableComboBox()
        self.port_combo.set_refresh_callback(self.refresh_ports)

        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("115200")

        self.refresh_ports()

        self.connect_btn = QPushButton("Connecter")
        self.auto_reconnect = QCheckBox("Reconnexion auto")

        self.auto_reconnect.toggled.connect(self.toggle_auto_reconnect)

        self.clear_btn = QPushButton("Effacer console")

        self.input_line = QLineEdit()
        self.send_btn = QPushButton("Envoyer")

        # --- Layout ---
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Port:"))
        top_layout.addWidget(self.port_combo)
        top_layout.addWidget(QLabel("Baudrate:"))
        top_layout.addWidget(self.baud_combo)
        top_layout.addWidget(self.connect_btn)
        top_layout.addWidget(self.auto_reconnect)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(self.send_btn)
        input_layout.addWidget(self.clear_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.text_area)
        main_layout.addLayout(input_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # --- Sérial worker ---
        self.worker = SerialWorker()
        self.worker.line_received.connect(self.display_line)
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.send_btn.clicked.connect(self.send_text)
        self.clear_btn.clicked.connect(self.text_area.clear)

        # --- Timer pour reconnexion ---
        self.reconnect_timer = QTimer()
        self.reconnect_timer.timeout.connect(self.try_reconnect)

    def toggle_auto_reconnect(self, checked: bool):
        if checked:
            self.reconnect_timer.start(2000)
            self.display_line("[Reconnexion automatique activée]")
        else:
            self.reconnect_timer.stop()
            self.display_line("[Reconnexion automatique désactivée]")


    def refresh_ports(self):
        current = self.port_combo.currentText()
        self.port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.addItems(ports)
    # Si on avait déjà un port sélectionné et il est encore dispo
        if current in ports:
            self.port_combo.setCurrentText(current)
        else:
        # Choisir un port par défaut hors /dev/ttySx
            for p in ports:
                if not p.startswith("/dev/ttyS"):
                    self.port_combo.setCurrentText(p)
                    break

    def toggle_connection(self):
        if self.connected:
            try:
                self.worker.disconnect()
                self.connect_btn.setText("Connecter")
                self.display_line("\n[Déconnecté]")
                self.reconnect_timer.stop()
            except Exception as e:
                self.display_line(f"[Erreur lors de la déconnexion] {e}")
            self.connected = False
            return
        else:
            port = self.port_combo.currentText()
            baud = int(self.baud_combo.currentText())
            if self.worker.connect(port, baud):
                self.connect_btn.setText("Déconnecter")
                self.display_line(f"[Connecté à {port} @ {baud}]\n")
                self.connected = True
                if self.auto_reconnect.isChecked():
                    self.reconnect_timer.start(2000)
            else:
                self.display_line("[Échec de connexion]\n")

    def try_reconnect(self):
        self.refresh_ports()
        if not self.worker.is_connected():
            port = self.port_combo.currentText()
            baud = int(self.baud_combo.currentText())
            self.worker.connect(port, baud)

    def send_text(self):
        text = self.input_line.text()
        if text:
            self.worker.send_line(text)
            self.input_line.clear()

    def display_line(self, line):
        from datetime import datetime

    # Génère le timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        time_html = f'<span style="color:#8be9fd;">[{timestamp}]</span>'

    # Couleur par défaut
        color = "#eeeeee"

    # Mise en forme spéciale si c’est un tag système seul, ex : [Déconnecté]
        if line.startswith("[") and line.endswith("]") and " " not in line:
            color = "#888888"
            line = f"<i>{line}</i>"

    # Analyse du contenu textuel pour choisir la couleur
        line_lower = line.lower()
        if "error" in line_lower or "erreur" in line_lower:
            color = "#ff5555"  # Rouge
        elif "ok" in line_lower or "succès" in line_lower or "connecté" in line_lower:
            color = "#50fa7b"  # Vert
        elif "avertissement" in line_lower or "warn" in line_lower:
            color = "#f1fa8c"  # Jaune

    # Priorité : log ESP-IDF → écrase la couleur précédente si présent
        if "[E]" in line:
            color = "#ff5555"
        elif "[W]" in line:
            color = "#f1fa8c"
        elif "[I]" in line:
            color = "#aaaaaa"
        elif "[D]" in line:
            color = "#8be9fd"
        elif "[V]" in line:
            color = "#666666"

    # Application du HTML final
        html = f'{time_html} <span style="color:{color};">{line}</span>'
        self.text_area.append(html)

