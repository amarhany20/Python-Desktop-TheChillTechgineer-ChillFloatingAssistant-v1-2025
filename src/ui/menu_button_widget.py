from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QEvent, QRect
from PySide6.QtGui import QPixmap, QIcon, QFontMetrics, QColor, QPainter

class MenuButtonWidget(QWidget):
    """
    A custom widget that displays:
      - An icon (or a placeholder if none is provided)
      - A two-line truncated text label
      - A hover effect that changes the background color
    """
    clicked = Signal()

    def __init__(self, icon: QIcon, text: str, parent=None):
        super().__init__(parent)
        self._icon_label = QLabel(self)
        self._text_label = QLabel(self)
        self._text_label.setWordWrap(True)
        self._text_label.setAlignment(Qt.AlignCenter | Qt.AlignTop)

        self._hovered = False
        self._normal_bg = QColor("#00000000")   # fully transparent
        self._hover_bg = QColor("#444444")        # darker hover color

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self._icon_label, 0, Qt.AlignCenter)
        layout.addWidget(self._text_label, 0, Qt.AlignCenter)

        self.set_icon(icon)
        truncated_text = self._truncate_to_two_lines(text, self._text_label.font(), 80)
        self._text_label.setText(truncated_text)
        self.setMouseTracking(True)

    def set_icon(self, icon: QIcon):
        pixmap = icon.pixmap(48, 48)
        if pixmap.isNull():
            placeholder_pixmap = QPixmap(48, 48)
            placeholder_pixmap.fill(QColor("#888888"))
            self._icon_label.setPixmap(placeholder_pixmap)
        else:
            self._icon_label.setPixmap(pixmap)

    def _truncate_to_two_lines(self, text: str, font, max_width: int) -> str:
        fm = QFontMetrics(font)
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = (current_line + " " + word).strip()
            if fm.horizontalAdvance(test_line) > max_width:
                lines.append(current_line)
                current_line = word
                if len(lines) == 2:
                    truncated = self._force_ellipsis(current_line, fm, max_width)
                    lines[-1] = truncated
                    return "\n".join(lines)
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)
        if len(lines) > 2:
            lines = lines[:2]
            lines[-1] = self._force_ellipsis(lines[-1], fm, max_width)
        if len(lines) == 1:
            if fm.horizontalAdvance(lines[0]) > max_width:
                lines[0] = self._force_ellipsis(lines[0], fm, max_width)
        return "\n".join(lines)

    def _force_ellipsis(self, text: str, fm: QFontMetrics, max_width: int) -> str:
        ellipsis = "..."
        while text and fm.horizontalAdvance(text + ellipsis) > max_width:
            text = text[:-1]
        return text + ellipsis

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self._hovered:
            painter.fillRect(self.rect(), self._hover_bg)
        else:
            painter.fillRect(self.rect(), self._normal_bg)
        super().paintEvent(event)
