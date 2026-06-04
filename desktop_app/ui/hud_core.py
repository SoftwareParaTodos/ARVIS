import math
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import QWidget


class HudCore(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.angle = 0
        self.pulse = 0
        self.state = "online"
        self.animations_enabled = True

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(30)

        self.setMinimumSize(360, 360)

    def set_state(self, state: str):
        self.state = state
        self.update()

    def set_animations_enabled(self, enabled: bool):
        self.animations_enabled = enabled
        self.update()

    def _tick(self):
        if self.animations_enabled:
            self.angle = (self.angle + 2) % 360
            self.pulse = (self.pulse + 0.06) % (math.pi * 2)
            self.update()

    def _state_text(self):
        if self.state == "listening":
            return "ESCUCHANDO"
        if self.state == "processing":
            return "PROCESANDO"
        if self.state == "responding":
            return "RESPONDIENDO"
        if self.state == "blocked":
            return "ACCIÓN BLOQUEADA"
        return "ARVIS EN LÍNEA"

    def _state_color(self):
        if self.state == "listening":
            return QColor("#00D4FF")
        if self.state == "processing":
            return QColor("#8B5CF6")
        if self.state == "responding":
            return QColor("#38BDF8")
        if self.state == "blocked":
            return QColor("#EF4444")
        return QColor("#38BDF8")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        base = min(w, h) * 0.38

        color = self._state_color()

        pulse_value = 1.0
        if self.animations_enabled:
            pulse_value = 1.0 + (math.sin(self.pulse) * 0.04)

        # Glow externo
        for i in range(8):
            alpha = max(12, 60 - i * 7)
            pen = QPen(QColor(color.red(), color.green(), color.blue(), alpha))
            pen.setWidth(2)
            painter.setPen(pen)
            r = base * pulse_value + i * 7
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # Aro principal
        pen = QPen(color)
        pen.setWidth(3)
        painter.setPen(pen)
        r = base
        painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # Aro interno
        inner = base * 0.63
        pen = QPen(QColor("#0EA5E9"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawEllipse(cx - inner, cy - inner, inner * 2, inner * 2)

        # Segmentos giratorios
        if self.animations_enabled:
            segment_pen = QPen(QColor("#7DD3FC"))
            segment_pen.setWidth(5)
            painter.setPen(segment_pen)

            rect_size = base * 2
            rect_x = cx - base
            rect_y = cy - base

            for offset in (0, 90, 180, 270):
                painter.drawArc(
                    int(rect_x),
                    int(rect_y),
                    int(rect_size),
                    int(rect_size),
                    int((self.angle + offset) * 16),
                    int(36 * 16),
                )

        # Líneas radiales cortas
        painter.setPen(QPen(QColor(56, 189, 248, 130), 1))
        for i in range(0, 360, 15):
            rad = math.radians(i + self.angle * 0.25)
            r1 = base * 1.08
            r2 = base * 1.15
            x1 = cx + math.cos(rad) * r1
            y1 = cy + math.sin(rad) * r1
            x2 = cx + math.cos(rad) * r2
            y2 = cy + math.sin(rad) * r2
            painter.drawLine(x1, y1, x2, y2)

        # Punto central
        painter.setBrush(QColor(color.red(), color.green(), color.blue(), 180))
        painter.setPen(Qt.NoPen)
        center_r = base * 0.12
        painter.drawEllipse(cx - center_r, cy - center_r, center_r * 2, center_r * 2)

        # Texto central
        painter.setPen(QColor("#E5F6FF"))
        font = QFont("Segoe UI", 15)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, self._state_text())

        # Subtexto
        painter.setPen(QColor("#8FB3C8"))
        small_font = QFont("Segoe UI", 9)
        painter.setFont(small_font)
        painter.drawText(
            0,
            int(cy + base * 0.33),
            w,
            30,
            Qt.AlignCenter,
            "Sistema operativo activo",
        )
