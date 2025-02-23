import json
import os


class SettingsManager:
    """
    Manages loading and saving settings from configuration files.

    It loads:
    - App configuration (static, from app_config.json)
    - Default settings (from default_settings.json)
    - User settings (from user_settings.json)

    It merges the default settings with the user settings so that any missing keys
    in the user settings are filled in with the defaults.
    """

    def __init__(self, config_dir='src/config'):
        self.config_dir = config_dir
        # Load app_config.json first.
        self.app_config_file = os.path.join(config_dir, 'app_config.json')
        self.app_config = self.load_json(self.app_config_file)

        # Get file paths from app_config's "config_paths" section (if available)
        config_paths = self.app_config.get("config_paths", {})
        self.user_settings_file = config_paths.get("user_settings", os.path.join(config_dir, 'user_settings.json'))
        self.default_settings_file = config_paths.get("default_settings",
                                                      os.path.join(config_dir, 'default_settings.json'))
        self.assets_config_file = config_paths.get("assets_config", os.path.join(config_dir, 'assets_config.json'))
        self.theme_colors_file = config_paths.get("theme_colors", os.path.join(config_dir, 'theme_colors.json'))

        # Load default and user settings
        self.default_settings = self.load_json(self.default_settings_file)
        self.user_settings = self.load_json(self.user_settings_file)

        # Merge default settings with user settings (user settings override defaults)
        self.settings = self.merge_settings(self.default_settings, self.user_settings)

    def load_json(self, filepath):
        """Loads a JSON file from the given path; returns an empty dict if not found or error."""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        else:
            return {}

    def merge_settings(self, default, user):
        """Merge default settings with user settings, giving precedence to user settings."""
        merged = default.copy()
        merged.update(user)
        return merged

    def get_setting(self, key, default=None):
        """Returns the effective setting value for a given key."""
        return self.settings.get(key, default)

    def update_setting(self, key, value):
        """
        Updates a specific setting.
        This updates both the in-memory merged settings and the user_settings.
        The change is then saved back to the user_settings.json file.
        """
        self.settings[key] = value
        self.user_settings[key] = value
        self.save_user_settings()

    def save_user_settings(self):
        """Saves the user settings back to the user_settings.json file."""
        with open(self.user_settings_file, 'w') as f:
            json.dump(self.user_settings, f, indent=4)

    def reload(self):
        """Reloads all settings from disk."""
        self.default_settings = self.load_json(self.default_settings_file)
        self.user_settings = self.load_json(self.user_settings_file)
        self.settings = self.merge_settings(self.default_settings, self.user_settings)
