from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PyQt6.QtWidgets import QApplication, QWidget


class CompanionOrb(QWidget):
    STATES = ("idle", "listening", "thinking", "speaking", "error", "hidden")

    PALETTES = {
        "idle": [(99, 102, 241), (139, 92, 246), (56, 189, 248)],
        "listening": [(99, 102, 241), (168, 85, 247), (34, 211, 238)],
        "thinking": [(14, 165, 233), (59, 130, 246), (129, 140, 248)],
        "speaking": [(45, 212, 191), (34, 197, 94), (56, 189, 248)],
        "error": [(248, 113, 113), (239, 68, 68), (251, 146, 60)],
    }

    def __init__(
        self,
        size: int = 72,
        orb_size: int = 56,
        left_margin: int = 28,
        bottom_margin: int = 28,
    ) -> None:
        super().__init__()
        self._size = size
        self._orb_size = orb_size
        self._left_margin = left_margin
        self._bottom_margin = bottom_margin
        self._state = "idle"
        self._phase = 0.0
        self._pulse = 0.0

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(size, size)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def reposition(self) -> None:
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geometry = screen.availableGeometry()
        x = geometry.x() + self._left_margin
        y = geometry.y() + geometry.height() - self._size - self._bottom_margin
        self.move(x, y)

    def set_state(self, state: str, _detail: str = "") -> None:
        if state not in self.STATES:
            state = "thinking"
        self._state = state
        if state == "hidden":
            self.hide()
        else:
            self.reposition()
            self.show()
            self.raise_()
        self.update()

    def _tick(self) -> None:
        speed = {
            "idle": 0.018,
            "listening": 0.065,
            "thinking": 0.035,
            "speaking": 0.048,
            "error": 0.05,
            "hidden": 0.01,
        }.get(self._state, 0.03)
        self._phase = (self._phase + speed) % math.tau
        self._pulse = (self._pulse + 0.07) % math.tau
        if self._state != "hidden":
            self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center = QPointF(self.width() / 2, self.height() / 2)
        orb_radius = self._orb_size / 2
        intensity = {
            "idle": 0.55,
            "listening": 1.0,
            "thinking": 0.85,
            "speaking": 0.9,
            "error": 0.95,
        }.get(self._state, 0.7)
        pulse = (math.sin(self._pulse) + 1) / 2
        glow_radius = orb_radius + 8 + pulse * (10 if self._state == "listening" else 5)

        glow = QRadialGradient(center, glow_radius)
        glow.setColorAt(0.0, QColor(255, 255, 255, int(30 * intensity)))
        glow.setColorAt(0.45, QColor(99, 102, 241, int(55 * intensity)))
        glow.setColorAt(1.0, QColor(99, 102, 241, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(center, glow_radius, glow_radius)

        clip_path = QPainterPath()
        clip_path.addEllipse(center, orb_radius, orb_radius)

        painter.save()
        painter.setClipPath(clip_path)

        base = QRadialGradient(center, orb_radius)
        base.setColorAt(0.0, QColor(255, 255, 255, int(210 * intensity)))
        base.setColorAt(0.35, QColor(226, 232, 240, int(120 * intensity)))
        base.setColorAt(1.0, QColor(15, 23, 42, int(220 * intensity)))
        painter.setBrush(QBrush(base))
        painter.drawEllipse(center, orb_radius, orb_radius)

        colors = self.PALETTES.get(self._state, self.PALETTES["idle"])
        blob_specs = [
            (0.0, 0.34, colors[0], 0.78),
            (2.1, 0.28, colors[1], 0.72),
            (4.2, 0.3, colors[2], 0.68),
        ]
        for offset, radius_factor, rgb, alpha in blob_specs:
            angle = self._phase + offset
            blob_center = QPointF(
                center.x() + math.cos(angle) * orb_radius * 0.28,
                center.y() + math.sin(angle) * orb_radius * 0.28,
            )
            blob_radius = orb_radius * radius_factor
            blob = QRadialGradient(blob_center, blob_radius)
            blob.setColorAt(0.0, QColor(*rgb, int(255 * alpha * intensity)))
            blob.setColorAt(0.55, QColor(*rgb, int(120 * alpha * intensity)))
            blob.setColorAt(1.0, QColor(*rgb, 0))
            painter.setBrush(QBrush(blob))
            painter.drawEllipse(blob_center, blob_radius, blob_radius)

        painter.restore()

        ring_alpha = int(90 + pulse * 70) if self._state == "listening" else int(55 + pulse * 35)
        ring = QPen(QColor(255, 255, 255, ring_alpha), 1.4)
        painter.setPen(ring)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, orb_radius - 1, orb_radius - 1)

        if self._state == "listening":
            arc_radius = orb_radius + 4 + pulse * 4
            arc_pen = QPen(QColor(255, 255, 255, int(120 + pulse * 80)), 2.0)
            arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(arc_pen)
            start_angle = int((self._phase * 180 / math.pi) * 16) % (360 * 16)
            painter.drawArc(
                int(center.x() - arc_radius),
                int(center.y() - arc_radius),
                int(arc_radius * 2),
                int(arc_radius * 2),
                start_angle,
                110 * 16,
            )

        highlight = QLinearGradient(
            QPointF(center.x() - orb_radius * 0.35, center.y() - orb_radius * 0.55),
            QPointF(center.x() + orb_radius * 0.2, center.y() + orb_radius * 0.1),
        )
        highlight.setColorAt(0.0, QColor(255, 255, 255, int(150 * intensity)))
        highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(highlight))
        painter.drawEllipse(
            QPointF(center.x() - orb_radius * 0.18, center.y() - orb_radius * 0.22),
            orb_radius * 0.22,
            orb_radius * 0.16,
        )


OverlayWindow = CompanionOrb
