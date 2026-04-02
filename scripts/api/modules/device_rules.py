import os
import json
import subprocess

SNAP_COMMON = os.environ.get('SNAP_COMMON', '/tmp')
LIMITS_CONFIG_PATH = os.path.join(SNAP_COMMON, 'config/device_limits.json')

def _run(cmd_list):
    try:
        subprocess.run(cmd_list, capture_output=True, text=True, check=False)
    except Exception as e:
        print(f"Error running {' '.join(cmd_list)}: {e}")

def load_limits():
    """Returns a dict of { mac_address: { "blocked": bool, "limit_mbps": float } }"""
    if os.path.exists(LIMITS_CONFIG_PATH):
        try:
            with open(LIMITS_CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load device limits: {e}")
    return {}

def save_limits(limits):
    os.makedirs(os.path.dirname(LIMITS_CONFIG_PATH), exist_ok=True)
    try:
        with open(LIMITS_CONFIG_PATH, 'w') as f:
            json.dump(limits, f, indent=2)
    except Exception as e:
        print(f"Failed to save device limits: {e}")

def get_limits():
    return load_limits()

def set_block(mac: str, blocked: bool):
    mac = mac.lower()
    limits = load_limits()
    if mac not in limits:
        limits[mac] = {}
    
    limits[mac]['blocked'] = blocked
    save_limits(limits)
    
    # Apply via iptables
    if blocked:
        # Drop FORWARD and INPUT traffic to prevent access to router or internet
        _run(["iptables", "-C", "FORWARD", "-m", "mac", "--mac-source", mac, "-j", "REJECT"])
        if subprocess.run(["iptables", "-C", "FORWARD", "-m", "mac", "--mac-source", mac, "-j", "REJECT"], capture_output=True).returncode != 0:
            _run(["iptables", "-I", "FORWARD", "-m", "mac", "--mac-source", mac, "-j", "REJECT"])
    else:
        # Unblock by removing rule iteratively in case there are multiple
        while subprocess.run(["iptables", "-C", "FORWARD", "-m", "mac", "--mac-source", mac, "-j", "REJECT"], capture_output=True).returncode == 0:
            _run(["iptables", "-D", "FORWARD", "-m", "mac", "--mac-source", mac, "-j", "REJECT"])

def set_speed_limit(mac: str, ip: str, interface: str, limit_mbps: float):
    mac = mac.lower()
    limits = load_limits()
    if mac not in limits:
        limits[mac] = {}
    
    limits[mac]['limit_mbps'] = limit_mbps
    limits[mac]['last_ip'] = ip
    limits[mac]['last_interface'] = interface
    save_limits(limits)
    
    apply_tc_limit(ip, interface, limit_mbps)

def apply_tc_limit(ip: str, interface: str, limit_mbps: float):
    if not interface or not ip:
        return
        
    # The interface should be the physical interface where the device is connected
    # Mini-PCs often bridge wireless and wired devices, but if wlan0 or wlo1 is used, apply there.
    
    # We will use class IDs derived from IP address (e.g. 192.168.1.150 -> classid 1:150)
    try:
        ip_last_octet = int(ip.split('.')[3])
    except:
        ip_last_octet = 999
        
    class_id = f"1:{ip_last_octet}"
    mark_id = ip_last_octet
    
    # Create root HTB if it doesn't exist
    has_qdisc = subprocess.run(["tc", "qdisc", "show", "dev", interface], capture_output=True, text=True)
    if not has_qdisc.stdout or "htb" not in has_qdisc.stdout:
        _run(["tc", "qdisc", "add", "dev", interface, "root", "handle", "1:", "htb", "default", "9999"])
        # Give unshaped traffic max link speed so it doesn't drop
        _run(["tc", "class", "add", "dev", interface, "parent", "1:", "classid", "1:9999", "htb", "rate", "1000mbit"])

    # First delete any existing class/filter for this device
    # (Since there's no easy tc delete class syntax without knowing exact details, we just ignore errors on add or try remove)
    _run(["tc", "filter", "del", "dev", interface, "parent", "1:", "protocol", "ip", "prio", "1", "u32", "match", "ip", "dst", ip])
    
    if limit_mbps <= 0:
        # Unlimited means we just delete the rule
        return

    # Add limits
    rate_str = f"{limit_mbps}mbit"
    
    # For outgoing traffic to device (Download for device)
    _run(["tc", "class", "replace", "dev", interface, "parent", "1:", "classid", class_id, "htb", "rate", rate_str, "ceil", rate_str])
    
    # Add filter linking IP to Class
    _run(["tc", "filter", "add", "dev", interface, "protocol", "ip", "parent", "1:", "prio", "1", "u32", "match", "ip", "dst", ip, "flowid", class_id])


def apply_all_startup():
    """Apply all persisted blocks and limits across known interfaces. Called when API starts."""
    limits = load_limits()
    for mac, cfg in limits.items():
        if cfg.get('blocked', False):
            set_block(mac, True)
            
        limit = cfg.get('limit_mbps', 0)
        ip = cfg.get('last_ip')
        iface = cfg.get('last_interface')
        if limit > 0 and ip and iface:
            apply_tc_limit(ip, iface, limit)
