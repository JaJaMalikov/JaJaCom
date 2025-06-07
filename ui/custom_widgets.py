from PySide6.QtWidgets import QComboBox


class RefreshableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.refresh_callback = None

    def set_refresh_callback(self, callback):
        self.refresh_callback = callback

    def showPopup(self):
        if self.refresh_callback:
            self.refresh_callback()
        super().showPopup()
