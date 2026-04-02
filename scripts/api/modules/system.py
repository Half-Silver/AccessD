import os
import subprocess
import time

def uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        return str(time.strftime('%H:%M:%S', time.gmtime(uptime_seconds)))

def LoadAvg1Min():
    with open('/proc/loadavg', 'r') as f:
        return float(f.readline().split()[0])

def systemLoadPercentage():
    # Roughly translate load average to percentage for 1 core
    # (Simplified for dashboard)
    return min(100.0, (LoadAvg1Min() / os.cpu_count()) * 100.0)

def usedMemory():
    with open('/proc/meminfo', 'r') as f:
        meminfo = {}
        for line in f:
            parts = line.split(':')
            if len(parts) == 2:
                meminfo[parts[0].strip()] = int(parts[1].split()[0])
        
        total = meminfo.get('MemTotal', 1)
        available = meminfo.get('MemAvailable', 0)
        used = total - available
        return (used / total) * 100.0

def systemTemperature():
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            return float(f.readline().strip()) / 1000.0
    except:
        return 0.0

def rpiRevision():
    # Extract model name for the model info field
    try:
        with open('/sys/firmware/devicetree/base/model', 'r') as f:
            return f.readline().strip('\x00')
    except:
        return "Generic Linux Device"

def systime():
    return time.strftime('%H:%M:%S')
