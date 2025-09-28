#!/usr/bin/env python3

##############################################################################
# Configuration management for Photo Tools application.
# This module defines a singleton Config class that handles loading,
# saving, and validating application configuration from a JSON file.
#
# For test and debugging purposes, the script can be run directly to
# create a default configuration file or print the current configuration.
##############################################################################

import json
import os
import argparse
from typing import Optional

# Singleton metaclass for Config
class _SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            # create the instance the first time
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=_SingletonMeta):
    KEY_DB_PATH = "db_path"
    KEY_IMAGE_EXTENSIONS = "image_extensions"
    VAL_DEFAULT_CONFIG_PATH = "./.cpig_config.json"
    VAL_DEFAULT_DB_PATH = "./cpig_database.db"
    VAL_DEFAULT_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
        
    """Configuration holder (singleton).

    Creating Config() multiple times returns the same instance. The first
    instantiation runs the normal initialization (optionally loading the
    provided config file). Subsequent instantiations return the same object
    and do not re-run __init__.
    """
    def __init__(self, path2config: Optional[str] = None):
        # __init__ will only run once for the singleton instance. If you need
        # to reload a different config file later, call load_config(...) on
        # the returned instance.
        if path2config is None:
            self.make_default_config()
        else:
            # accept an optional path to the config file
            self.load_config(path2config)

    def make_default_config(self) -> None:
        """Create default configuration."""
        self.path_to_cfg = self.VAL_DEFAULT_CONFIG_PATH
        self.db_path = self.VAL_DEFAULT_DB_PATH
        self.image_extensions = self.VAL_DEFAULT_IMAGE_EXTENSIONS
        self.settings = {
            "db_path": self.db_path,
            "image_extensions": self.image_extensions,
        }

    def save_config(self) -> None:
        """Save configuration to json file."""
        self.__update_setting__()
        with open(self.path_to_cfg, 'w') as config_file:
            json.dump(self.settings, config_file, indent=4)
        print(f"Configuration saved to {self.path_to_cfg}.")
        config_file.close()

    def load_config(self, path2config: Optional[str] = None) -> bool:
        """Load configuration from json file.

        If path2config is provided, set it as the config file path before
        attempting to load.
        """
        if path2config is not None:
            self.path_to_cfg = path2config

        if not os.path.exists(self.path_to_cfg):
            return False
        try:
            with open(self.path_to_cfg, 'r') as config_file:
                self.settings = json.load(config_file)
        except (json.JSONDecodeError, IOError):
            return False

        if not self.check_config():
            return False

        self.db_path = self.settings.get("db_path", None)
        self.image_extensions = self.settings.get("image_extensions", [])

        return True

    # Configuration Validation
    def check_config(self) -> bool:
        """Check if all required settings are present."""
        if getattr(self, 'settings', None) is None:
            return False
        if self.settings.get("db_path", None) is None:
            return False
        if self.settings.get("image_extensions", None) is None:
            return False
        return True

    def __update_setting__(self) -> None:
        """Update a configuration setting and reflect it in the settings dict."""
        self.settings[self.KEY_DB_PATH] = self.db_path
        self.settings[self.KEY_IMAGE_EXTENSIONS] = self.image_extensions
                
    def print_config(self) -> None:
        """Print current configuration to console."""
        print (f"path_to_cfg: {self.path_to_cfg}")
        print (f"db_path: {self.db_path}")
        print (f"image_extensions: {self.image_extensions}")

    # Getter Methods
    def get_db_path(self) -> str:
        '''return the database path from the configuration'''
        return self.db_path

    def get_image_extensions(self) -> list:
        '''return the list of image extensions from the configuration'''
        return self.image_extensions

# Script entry point

def main():
    args = get_args()
    
    if args.make_default:
        config = Config(args.config)
        config.make_default_config()
        config.save_config()
        exit(0)
    
    if args.config:
        config = Config(args.config)
        config.print_config()
    else:
        print (f"Make default config {Config.VAL_DEFAULT_CONFIG_PATH}")
        config = Config()
        config.save_config()
        config.print_config()
            
def get_args():
    parser = argparse.ArgumentParser(description="Photo Tools Configuration")
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--make_default', action='store_true', help='Create default configuration file')
    return parser.parse_args()
    
if __name__ == "__main__":
    main()