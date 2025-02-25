import json
import os
from typing import Any, Dict, Optional

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QGuiApplication, QImage, QImageReader, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from src.state.state_manager import StateManager


class FloatingWidget(QWidget):
    def __init__(self, state_manager: StateManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.state_manager: StateManager = state_manager
        # Read config from app_config
        app_config = self.state_manager.settings_manager.app_config
        self.min_size: int = app_config.get("min_widget_size", 32)
        self.max_size: int = app_config.get("max_widget_size", 200)
        self.handle_size: int = app_config.get("resize_handle_size", 20)
        self.debug: bool = app_config.get("debug", False)
        self.show_debug_borders: bool = app_config.get("show_debug_borders", False)

        # From user settings: whether to show the resize icon
        self.show_resize_icon: bool = self.state_manager.settings_manager.get_setting("show_widget_resize_icon", True)

        # Set window flags and transparency
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Enable mouse tracking so we can detect hover without pressing any buttons
        self.setMouseTracking(True)

        # Drag/Resize states
        self.dragging: bool = False
        self.resizing: bool = False
        self.drag_offset: QPoint = QPoint(0, 0)
        self.resize_origin: QPoint = QPoint(0, 0)
        self.original_size: QRect = QRect()

        # Placeholders for original images
        self.original_image: Optional[QImage] = None
        self.original_handle_icon: Optional[QPixmap] = None

        # Load main icon
        self.selected_icon: Optional[QPixmap] = self.load_main_icon()

        # Determine final widget size from user settings ("last_widget_size")
        last_widget_size = self.state_manager.settings_manager.get_setting("last_widget_size", 64)
        widget_size = max(self.min_size, min(last_widget_size, self.max_size))
        if self.selected_icon and self.original_image:
            self._scale_main_icon(widget_size)
        else:
            self.setFixedSize(widget_size, widget_size)

        # Load custom resize handle icon (this will be updated in _scale_main_icon)
        self.handle_pixmap: Optional[QPixmap] = self.load_resize_icon()

        # Set initial position
        last_pos: Dict[str, Any] = self.state_manager.settings_manager.get_setting(
            "last_position", {"x": 100, "y": 100}
        )
        self.move(last_pos.get("x", 100), last_pos.get("y", 100))

        # Flag for menu toggling
        self.menu_toggled: bool = False

    def load_main_icon(self) -> Optional[QPixmap]:
        """
        Loads the main icon from assets_config.json without pre-scaling,
        so that the original high-resolution image is preserved.
        """
        assets_path = self.state_manager.settings_manager.assets_config_file
        if not os.path.exists(assets_path):
            if self.debug:
                print("Assets config file not found:", assets_path)
            return None

        with open(assets_path, "r") as f:
            asset_config = json.load(f)

        selected_key = self.state_manager.settings_manager.get_setting("selected_widget_icon", "main_icon_1")
        icon_path = asset_config.get(selected_key)
        if not icon_path or not os.path.exists(icon_path):
            if self.debug:
                print("Icon path not found:", icon_path)
            return None

        # Read the image using QImageReader without scaling it first.
        reader = QImageReader(icon_path)
        reader.setAutoTransform(True)
        image = reader.read()
        if image.isNull():
            if self.debug:
                print("Failed to load image from:", icon_path)
            return None

        # Save the original high-resolution image for later rescaling.
        self.original_image = image

        # Create a pixmap from the full resolution image.
        pixmap = QPixmap.fromImage(image)
        pixmap.setDevicePixelRatio(self.devicePixelRatioF())
        return pixmap

    def load_resize_icon(self) -> Optional[QPixmap]:
        """
        Loads the custom resize icon from assets_config.json and stores its original pixmap.
        It will be scaled later based on the widget size and a scale factor.
        """
        if not self.show_resize_icon:
            return None

        assets_path = self.state_manager.settings_manager.assets_config_file
        if not os.path.exists(assets_path):
            return None

        with open(assets_path, "r") as f:
            asset_config = json.load(f)
        resize_icon_path = asset_config.get("resize_icon_1")
        if resize_icon_path and os.path.exists(resize_icon_path):
            original_handle_icon = QPixmap(resize_icon_path)
            self.original_handle_icon = original_handle_icon  # Save for dynamic rescaling
            # Initially scale based on the current widget width:
            resize_icon_scale_factor = self.state_manager.settings_manager.app_config.get("resize_icon_scale_factor", 0.2)
            final_handle_icon_size = max(10, int(self.width() * resize_icon_scale_factor))
            return original_handle_icon.scaled(final_handle_icon_size, final_handle_icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return None

    def _scale_main_icon(self, widget_size: int) -> None:
        """
        Scales the main icon based on the widget size and updates the widget.
        Also dynamically rescales the custom resize handle icon using the configured scale factor.
        """
        if not self.original_image:
            return

        dpr: float = self.devicePixelRatioF()
        target_size: int = int(widget_size * dpr)
        scaled_image: QImage = self.original_image.scaled(
            target_size, target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        pixmap: QPixmap = QPixmap.fromImage(scaled_image)
        pixmap.setDevicePixelRatio(dpr)
        self.selected_icon = pixmap

        # Set widget size to the main icon's logical size:
        logical_size = pixmap.size() / pixmap.devicePixelRatio()
        self.setFixedSize(logical_size)

        # Now update the resize handle icon based on the new widget size:
        if self.show_resize_icon and self.original_handle_icon:
            resize_icon_scale_factor = self.state_manager.settings_manager.app_config.get("resize_icon_scale_factor", 0.2)
            # Compute the new handle size relative to the widget's width:
            final_handle_icon_size = max(10, int(self.width() * resize_icon_scale_factor))
            self.handle_pixmap = self.original_handle_icon.scaled(final_handle_icon_size, final_handle_icon_size,
                                                                   Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def _get_handle_rect(self) -> QRect:
        """
        Returns the rectangle for the resize handle drawn in the bottom-right corner.
        """
        if not self.show_resize_icon or not self.handle_pixmap:
            return QRect()
        w = min(self.handle_pixmap.width(), self.width())
        h = min(self.handle_pixmap.height(), self.height())
        x = self.width() - w
        y = self.height() - h
        return QRect(x, y, w, h)

    def _in_resize_handle(self, pos: QPoint) -> bool:
        """
        Checks if the given local position is within the resize handle area.
        """
        if not self.show_resize_icon or not self.handle_pixmap:
            return False
        return self._get_handle_rect().contains(pos)

    def paintEvent(self, event) -> None:
        """
        Paints the main icon and, if enabled, the custom resize handle.
        """
        painter = QPainter(self)
        if self.selected_icon:
            painter.drawPixmap(0, 0, self.selected_icon)
        else:
            painter.fillRect(self.rect(), Qt.gray)

        if self.show_resize_icon and self.handle_pixmap:
            handle_rect = self._get_handle_rect()
            if not handle_rect.isEmpty():
                painter.drawPixmap(handle_rect, self.handle_pixmap)

        if self.debug and self.show_debug_borders:
            pen = QPen(Qt.red, 2)
            painter.setPen(pen)
            painter.drawRect(self.rect())
            if self.show_resize_icon and self.handle_pixmap:
                pen = QPen(Qt.blue, 2)
                painter.setPen(pen)
                painter.drawRect(self._get_handle_rect())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            local_pos = event.position().toPoint()
            if self._in_resize_handle(local_pos):
                self.resizing = True
                self.resize_origin = event.globalPosition().toPoint()
                self.original_size = self.geometry()
            elif not self.menu_toggled:
                self.dragging = True
                self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.resizing:
            diff = event.globalPosition().toPoint() - self.resize_origin
            new_size = self.original_size.width() + diff.x()
            new_size = max(self.min_size, min(new_size, self.max_size))
            self.setFixedSize(new_size, new_size)
            if self.original_image:
                self._scale_main_icon(new_size)
        elif self.dragging and not self.menu_toggled:
            new_pos = event.globalPosition().toPoint() - self.drag_offset
            screen = QGuiApplication.screenAt(new_pos)
            if screen is None:
                screen = self.screen()
            screen_geom = screen.availableGeometry()
            margin = 50
            new_x = max(screen_geom.left() + margin,
                        min(new_pos.x(), screen_geom.right() - self.width() - margin))
            new_y = max(screen_geom.top() + margin,
                        min(new_pos.y(), screen_geom.bottom() - self.height() - margin))
            self.move(new_x, new_y)
        else:
            # Change the cursor when hovering over the resize handle
            local_pos = event.position().toPoint()
            if self._in_resize_handle(local_pos):
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            if self.resizing:
                self.resizing = False
                new_size = self.width()
                self.state_manager.settings_manager.update_setting("last_widget_size", new_size)
            elif self.dragging:
                self.dragging = False
                pos = self.pos()
                self.state_manager.settings_manager.update_setting("last_position", {"x": pos.x(), "y": pos.y()})
        super().mouseReleaseEvent(event)

    def set_menu_toggled(self, toggled: bool) -> None:
        self.menu_toggled = toggled

    def enterEvent(self, event: QMouseEvent) -> None:
        """
        Decrease the widget's opacity on mouse hover.
        """
        hover_opacity = self.state_manager.settings_manager.app_config.get("widget_hover_opacity", 0.5)
        self.setWindowOpacity(hover_opacity)
        super().enterEvent(event)

    def leaveEvent(self, event: QMouseEvent) -> None:
        """
        Restore the widget's opacity when the mouse is no longer hovering.
        """
        self.setWindowOpacity(1.0)
        super().leaveEvent(event)
