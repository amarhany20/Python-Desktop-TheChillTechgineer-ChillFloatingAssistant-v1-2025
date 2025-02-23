from src.core.settings_manager import SettingsManager


class StateManager:
    """
    Manages global app state, including theme, widget position, and other runtime settings.

    This class uses the SettingsManager to load configurations and provides helper methods
    to update or reload settings as the user interacts with the app.
    """

    def __init__(self):
        # Initialize settings manager
        self.settings_manager = SettingsManager()
        self.app_config = self.settings_manager.app_config
        self.settings = self.settings_manager.settings

        # Initialize runtime state from settings
        self.current_theme = self.settings.get('theme', 'dark-1')
        self.last_position = self.settings.get('last_position', {'x': 100, 'y': 100})

    def reload_settings(self):
        """Reload settings from disk, refreshing local state."""
        self.settings_manager.reload()
        self.settings = self.settings_manager.settings
        self.current_theme = self.settings.get('theme', 'dark-1')
        self.last_position = self.settings.get('last_position', {'x': 100, 'y': 100})
