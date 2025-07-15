import json
import os

from PySide6.QtWidgets import QWidget, QGridLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QIcon

from src.ui.menu_button_widget import MenuButtonWidget  # Our custom button widget

class MainMenu(QWidget):
    def __init__(self, state_manager, parent=None) -> None:
        super().__init__(parent)
        self.state_manager = state_manager

        app_config = self.state_manager.settings_manager.app_config
        user_settings = self.state_manager.settings_manager.user_settings

        # Load theme colors
        theme_colors_path = self.state_manager.settings_manager.theme_colors_file
        try:
            with open(theme_colors_path, "r") as f:
                all_themes = json.load(f)
        except Exception:
            all_themes = {}
        theme_name = user_settings.get("theme", "dark-1")
        theme = all_themes.get(theme_name, {})
        background_color = theme.get("background", "#333333")

        # Grid configuration
        grid_config = app_config.get("menu_grid", {"rows": 3, "columns": 3})
        self.rows = grid_config.get("rows", 3)
        self.columns = grid_config.get("columns", 3)

        # Menu size
        menu_size_options = app_config.get("menu_size_options",
            {"small": [250, 350], "medium": [300, 400], "large": [350, 450]})
        menu_size_key = user_settings.get("menu_size", "medium")
        size_option = menu_size_options.get(menu_size_key, [300, 400])
        self.menu_width, self.menu_height = size_option[0], size_option[1]

        # Tools list: prepend "settings" as the first tool.
        self.available_tools = ["settings"] + app_config.get("available_tools", [])

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setFixedSize(self.menu_width, self.menu_height)
        self.setStyleSheet(f"background-color: {background_color};")

        self.setup_ui()
        self.original_floating_pos = None
        self.owner = None  # To keep a reference to the owning FloatingWidget

    def setup_ui(self) -> None:
        layout = QGridLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        total_cells = self.rows * self.columns
        for index in range(total_cells):
            row = index // self.columns
            col = index % self.columns
            if index < len(self.available_tools):
                tool_name = self.available_tools[index]
                display_text = tool_name.replace("_", " ").title()
                icon_path = self._get_icon_path(tool_name)
                icon = QIcon(icon_path) if icon_path else QIcon()
                cell_widget = MenuButtonWidget(icon, display_text)
                cell_width = self.menu_width // self.columns - 20
                cell_height = self.menu_height // self.rows - 20
                cell_widget.setFixedSize(cell_width, cell_height)
                layout.addWidget(cell_widget, row, col)
            else:
                layout.addWidget(QWidget(self), row, col)
        self.setLayout(layout)

    def _get_icon_path(self, tool_name: str) -> str:
        asset_config_path = self.state_manager.settings_manager.assets_config_file
        if not os.path.exists(asset_config_path):
            return ""
        try:
            with open(asset_config_path, "r") as f:
                asset_config = json.load(f)
        except Exception:
            asset_config = {}
        theme_name : str = self.state_manager.settings_manager.get_setting("theme", "dark-1")
        if theme_name.__contains__("light"):
            icon_key = f"{tool_name}_icon_light"
        else: 
            icon_key = f"{tool_name}_icon_dark"
        return asset_config.get(icon_key, "")

    def show_below_widget(self, floating_widget: QWidget) -> None:
        self.owner = floating_widget  # Store reference to the owning widget
        self.original_floating_pos = floating_widget.pos()
        fw_geom = floating_widget.geometry()
        desired_x = fw_geom.left()
        desired_y = fw_geom.bottom()
        screen = QGuiApplication.screenAt(floating_widget.pos())
        if not screen:
            screen = QGuiApplication.primaryScreen()
        screen_geom = screen.availableGeometry()
        if desired_x + self.menu_width > screen_geom.right():
            desired_x = screen_geom.right() - self.menu_width - 10
        if desired_y + self.menu_height > screen_geom.bottom():
            new_fw_y = screen_geom.bottom() - self.menu_height - 10 - fw_geom.height()
            floating_widget.move(floating_widget.x(), new_fw_y)
            desired_y = floating_widget.geometry().bottom()
        self.move(desired_x, desired_y)
        self.show()
        self.raise_()
        self.setFocus()  # Ensure the menu gets focus so focusOutEvent works

    def focusOutEvent(self, event) -> None:
        # When the menu loses focus, hide it and update state accordingly.
        if self.owner:
            self.hide_menu(self.owner)
            self.owner.menu_toggled = False
            self.owner.state_manager.menu_open = False
        super().focusOutEvent(event)

    def hide_menu(self, floating_widget: QWidget) -> None:
        self.hide()
        if self.original_floating_pos:
            floating_widget.move(self.original_floating_pos)
