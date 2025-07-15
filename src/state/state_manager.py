from src.core.settings_manager import SettingsManager

class StateManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        self.settings_manager = SettingsManager()
        self.app_config = self.settings_manager.app_config
        self.settings = self.settings_manager.settings
        self.current_theme = self.settings.get('theme', 'dark-1')
        self.last_position = self.settings.get('last_position', {'x': 100, 'y': 100})
        self.menu_open = False  # New flag to track if the menu is open
        self.initialized = True

    def reload_settings(self):
        self.settings_manager.reload()
        self.settings = self.settings_manager.settings
        self.current_theme = self.settings.get('theme', 'dark-1')
        self.last_position = self.settings.get('last_position', {'x': 100, 'y': 100})
