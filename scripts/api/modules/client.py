import os
import json

def get_leases_path():
    SNAP_COMMON = os.environ.get('SNAP_COMMON', '/var/snap/accessd/common')
    return os.path.join(SNAP_COMMON, 'leases/dnsmasq.leases')

def get_active_clients():
    path = get_leases_path()
    clients = []
    if os.path.exists(path):
        with open(path, 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 4:
                    clients.append({
                        "mac": parts[1],
                        "ip": parts[2],
                        "hostname": parts[3],
                        "interface": "wlan0" # Default for hostapd usually
                    })
    return json.dumps(clients)
