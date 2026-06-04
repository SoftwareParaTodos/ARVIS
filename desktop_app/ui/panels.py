try:
    import psutil
except Exception:
    psutil = None

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class HudPanel(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("HudPanel")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 12, 14, 12)
        self.layout.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("PanelTitle")
        self.layout.addWidget(self.title_label)

    def add_line(self, text: str, object_name: str | None = None):
        label = QLabel(text)
        label.setWordWrap(True)
        if object_name:
            label.setObjectName(object_name)
        self.layout.addWidget(label)
        return label


class SystemPanel(HudPanel):
    def __init__(self, parent=None):
        super().__init__("SISTEMA", parent)

        self.cpu_label = self.add_line("CPU: --")
        self.ram_label = self.add_line("RAM: --")
        self.disk_label = self.add_line("Disco: --")
        self.backend_label = self.add_line("Backend: verificando...")
        self.backend_label.setObjectName("StatusYellow")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1200)

        self.refresh()

    def refresh(self):
        if psutil is None:
            self.cpu_label.setText("CPU: psutil no instalado")
            self.ram_label.setText("RAM: psutil no instalado")
            self.disk_label.setText("Disco: psutil no instalado")
            return

        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage("C:\\").percent

            self.cpu_label.setText(f"CPU: {cpu:.0f}%")
            self.ram_label.setText(f"RAM: {ram:.0f}%")
            self.disk_label.setText(f"Disco C: {disk:.0f}%")
        except Exception:
            self.cpu_label.setText("CPU: no disponible")
            self.ram_label.setText("RAM: no disponible")
            self.disk_label.setText("Disco: no disponible")

    def set_backend_status(self, online: bool):
        if online:
            self.backend_label.setText("Backend: conectado")
            self.backend_label.setObjectName("StatusGreen")
        else:
            self.backend_label.setText("Backend: sin conexión")
            self.backend_label.setObjectName("StatusYellow")
        self.backend_label.style().unpolish(self.backend_label)
        self.backend_label.style().polish(self.backend_label)


class ToolsPanel(HudPanel):
    def __init__(self, parent=None):
        super().__init__("HERRAMIENTAS", parent)

        self.add_line("• Abrir programas")
        self.add_line("• Buscar archivos")
        self.add_line("• Notas")
        self.add_line("• Memoria local")
        self.add_line("• Info del sistema")


class SecurityPanel(HudPanel):
    def __init__(self, parent=None):
        super().__init__("SEGURIDAD", parent)

        self.safe_label = self.add_line("Seguro: acciones simples", "StatusGreen")
        self.confirm_label = self.add_line("Confirmar: acciones sensibles", "StatusYellow")
        self.blocked_label = self.add_line("Bloqueado: acciones peligrosas", "StatusRed")


class LocalPanel(HudPanel):
    def __init__(self, parent=None):
        super().__init__("LOCAL", parent)

        self.add_line("Ubicación: Trelew / Chubut")
        self.add_line("Clima: pendiente")
        self.add_line("Red local: preparada")
