import os
import re

def get_conf_path():
    SNAP_COMMON = os.environ.get('SNAP_COMMON', '/var/snap/accessd/common')
    return os.path.join(SNAP_COMMON, 'config/hostapd.conf')

def get_conf_val(key):
    path = get_conf_path()
    if not os.path.exists(path):
        return "Unknown"
    with open(path, 'r') as f:
        for line in f:
            if line.startswith(f"{key}="):
                return line.split('=')[1].strip()
    return "Unknown"

def ssid():
    return get_conf_val("ssid")

def channel():
    return get_conf_val("channel")

def hw_mode():
    return get_conf_val("hw_mode")

def country_code():
    return get_conf_val("country_code")
