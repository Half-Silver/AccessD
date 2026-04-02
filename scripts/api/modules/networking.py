import os
import json
import time

def interfaces():
    # Simple interface list from /proc/net/dev
    ifaces = []
    try:
        with open('/proc/net/dev', 'r') as f:
            lines = f.readlines()[2:]
            for line in lines:
                name = line.split(':')[0].strip()
                if name == "lo": continue
                # We can't easily get IP here without ip addr show or sockets
                # But we can try to find it for common interfaces
                ifaces.append({
                    "interface": name,
                    "state": "up" # Assume up if in /proc/net/dev
                })
    except:
        pass
    return json.dumps(ifaces)

_last_stats = {}
_last_time = 0

def throughput():
    global _last_stats, _last_time
    now = time.time()
    dt = now - _last_time
    
    current_stats = {}
    try:
        with open('/proc/net/dev', 'r') as f:
            lines = f.readlines()[2:]
            for line in lines:
                parts = line.split(':')
                name = parts[0].strip()
                data = parts[1].split()
                current_stats[name] = {
                    'rx': int(data[0]),
                    'tx': int(data[8])
                }
    except:
        return "{}"

    results = {}
    if _last_stats and dt > 0:
        for name in current_stats:
            if name in _last_stats:
                results[name] = {
                    'rx': (current_stats[name]['rx'] - _last_stats[name]['rx']) / dt,
                    'tx': (current_stats[name]['tx'] - _last_stats[name]['tx']) / dt
                }
    
    _last_stats = current_stats
    _last_time = now
    return json.dumps(results)
