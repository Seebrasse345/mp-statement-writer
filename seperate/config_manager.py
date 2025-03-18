import configparser
import os
from tkinter import messagebox
from error_handler import log_error

def save_api_settings(api_key, model, window=None):
    """Save API settings to config file"""
    try:
        config = configparser.ConfigParser()
        
        # Load existing config
        if os.path.exists('config.ini'):
            config.read('config.ini')
        
        # Check if API section exists
        if 'API' not in config:
            config['API'] = {}
        
        # Update only if changed and not empty
        if api_key and not api_key.startswith('•'):
            config['API']['OPENAI_API_KEY'] = api_key
        
        # Update model
        config['API']['MODEL'] = model
        
        # Save config
        with open('config.ini', 'w') as f:
            config.write(f)
        
        messagebox.showinfo("Settings Saved", "API settings have been saved.")
        if window:
            window.destroy()
        
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
        log_error("Save API settings error", e)
        return False

def get_config_value(section, key, default=None):
    """Get a value from the config file"""
    try:
        config = configparser.ConfigParser()
        
        if not os.path.exists('config.ini'):
            return default
            
        config.read('config.ini')
        
        if section in config and key in config[section]:
            return config[section][key]
        else:
            return default
    except Exception as e:
        log_error("Get config value error", e)
        return default

def ensure_config_exists():
    """Make sure the config file exists with default values"""
    try:
        if not os.path.exists('config.ini'):
            config = configparser.ConfigParser()
            config['API'] = {
                'OPENAI_API_KEY': 'your_api_key_here',
                'MODEL': 'gpt-4o'
            }
            with open('config.ini', 'w') as f:
                config.write(f)
            return False
        return True
    except Exception as e:
        log_error("Config check error", e)
        return False