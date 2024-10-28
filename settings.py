import hashlib
import json
import os

SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {"mode": "off", "color": "red", "brightness": 100, "speed": 20}

def load_settings():
    if SETTINGS_FILE in os.listdir():
        with open(SETTINGS_FILE, 'r') as file:
            return json.load(file)
    return DEFAULT_SETTINGS

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as file:
        json.dump(settings, file)
        
def hash_settings(settings):
    json_string = json.dumps(settings)
    sha1 = hashlib.sha1(json_string)
    return sha1.digest()
