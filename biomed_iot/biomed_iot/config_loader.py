"""
The Config and ConfigSection classes simplify managing and accessing
settings from the config.toml file.

Config reads the configuration from a file
(by default, "/etc/biomed-iot/config.toml") and sets up each main section
(e.g. [host] within the toml file] using ConfigSection. This makes the settings
from the TOML file's sections and sub-sections easily accessible via dot
notation (like config.section.setting).
"""

import tomllib


class ConfigSection:
    def __init__(self, data):
        self.data = data

    def __getattr__(self, item):
        try:
            # If the value is a dict, convert it into another ConfigSection object
            value = self.data[item]
            if isinstance(value, dict):
                return ConfigSection(value)
            return value
        except KeyError:
            raise AttributeError(f'Key {item} not found.')


class Config:
    def __init__(self, config_path='/etc/biomed-iot/config.toml'):
        config_data = self.load_config(config_path)
        # Initialize the top level of the configuration data with ConfigSection
        for key, value in config_data.items():
            setattr(self, key, ConfigSection(value))

    def load_config(self, config_path):
        with open(config_path, 'rb') as config_file:
            return tomllib.load(config_file)


# Instance of the Config class
config = Config()
