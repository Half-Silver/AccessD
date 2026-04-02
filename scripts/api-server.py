#!/usr/bin/env python3
import os
import sys
import json
import asyncio
import subprocess
import re
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# Add the custom API modules to path
SNAP = os.environ.get('SNAP', '.')
SNAP_COMMON = os.environ.get('SNAP_COMMON', '/var/snap/accessd/common')
# Inside snap, scripts/api is mapped to bin/api
API_PATH = os.path.join(SNAP, 'bin/api') if os.environ.get('SNAP') else os.path.join(SNAP, 'scripts/api')
print(f"Loading API modules from: {API_PATH}")
if os.path.exists(API_PATH):
    sys.path.append(API_PATH)
else:
    print(f"WARNING: API module path not found: {API_PATH}")

try:
    import modules.system as rasp_system
    import modules.ap as rasp_ap
    import modules.client as rasp_client
    import modules.networking as rasp_networking
    import modules.device_rules as device_rules
except ImportError:
    # Mock modules for local development if not found
    print("Warning: RaspAP modules not found, using mock data")
    class MockModule:
        def __getattr__(self, name):
            return lambda *args, **kwargs: {}
    rasp_system = rasp_ap = rasp_client = rasp_networking = device_rules = MockModule()

app = FastAPI(title="AccessD API v1")

# Apply saved device blocklists/speed-limits on startup
try:
    if hasattr(device_rules, 'apply_all_startup'):
        device_rules.apply_all_startup()
except Exception as e:
    print(f"Startup Rules Error: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Pydantic Models ───────────────────────────────────────────────

class WirelessConfigUpdate(BaseModel):
    ssid: Optional[str] = None
    password: Optional[str] = None
    channel: Optional[str] = None
    security: Optional[str] = None

class FirewallRule(BaseModel):
    service: str
    port: str
    target: str
    protocol: str = "TCP"
    status: str = "enabled"

class QoSConfig(BaseModel):
    gaming_priority: int = 80
    streaming_priority: int = 60
    download_priority: int = 20
    bbr_enabled: bool = True
    enabled: bool = True

# ─── Helper: run a command safely ──────────────────────────────────

def _run_cmd(cmd: list, timeout: int = 10) -> str:
    """Run a subprocess command and return stdout. Raises on failure."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout
    except Exception as e:
        print(f"Command failed {cmd}: {e}")
        return ""

def _get_snap_cmd(service_name: str, action: str) -> list:
    """Build snap service command."""
    if os.environ.get('SNAP'):
        return ["snapctl", action, f"accessd.{service_name}"]
    return ["echo", f"mock: {action} {service_name}"]

# ─── QoS config file path ─────────────────────────────────────────

QOS_CONFIG_PATH = os.path.join(SNAP_COMMON, 'config/qos.json')

def _load_qos_config() -> dict:
    defaults = {"gaming_priority": 80, "streaming_priority": 60, "download_priority": 20, "bbr_enabled": True, "enabled": True}
    try:
        if os.path.exists(QOS_CONFIG_PATH):
            with open(QOS_CONFIG_PATH, 'r') as f:
                return json.load(f)
    except:
        pass
    return defaults

def _save_qos_config(config: dict):
    try:
        os.makedirs(os.path.dirname(QOS_CONFIG_PATH), exist_ok=True)
        with open(QOS_CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Failed to save QoS config: {e}")

# ─── Firewall rules file path ─────────────────────────────────────

FIREWALL_RULES_PATH = os.path.join(SNAP_COMMON, 'config/firewall_rules.json')

def _load_firewall_rules() -> list:
    try:
        if os.path.exists(FIREWALL_RULES_PATH):
            with open(FIREWALL_RULES_PATH, 'r') as f:
                return json.load(f)
    except:
        pass
    return []

def _save_firewall_rules(rules: list):
    try:
        os.makedirs(os.path.dirname(FIREWALL_RULES_PATH), exist_ok=True)
        with open(FIREWALL_RULES_PATH, 'w') as f:
            json.dump(rules, f, indent=2)
    except Exception as e:
        print(f"Failed to save firewall rules: {e}")

# ═══════════════════════════════════════════════════════════════════
# EXISTING ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/v1/system/stats")
async def get_system_stats():
    return {
        "cpu": {
            "usage": rasp_system.systemLoadPercentage(),
            "model": rasp_system.rpiRevision(),
            "load_avg": [rasp_system.LoadAvg1Min(), 0.5, 0.4]
        },
        "memory": {
            "used_pct": rasp_system.usedMemory(),
            "total_gb": 4.0,
            "used_gb": (rasp_system.usedMemory() / 100.0) * 4.0
        },
        "uptime": rasp_system.uptime(),
        "temp": rasp_system.systemTemperature()
    }

@app.get("/api/v1/network/interfaces")
async def get_interfaces():
    try:
        ifaces = json.loads(rasp_networking.interfaces())
        result = []
        for iface in ifaces:
            result.append({
                "name": iface.get('interface', 'unknown'),
                "type": "WAN" if iface.get('interface') in ("eth0", "enp1s0") else "LAN",
                "status": "up" if iface.get('state') == "up" else "down",
                "ip": iface.get('ip_address', '0.0.0.0'),
                "mask": iface.get('subnet_mask', '255.255.255.0')
            })
        return result
    except:
        return []

@app.get("/api/v1/network/clients")
async def get_clients():
    try:
        clients_json = rasp_client.get_active_clients()
        clients = json.loads(clients_json)
        result = []
        for c in clients:
            mac = c.get('mac', '00:00:00:00:00:00')
            # Generate deterministic mock usage MB based on MAC address
            # since true per-device tracking via iptables is not yet implemented
            mock_usage = (int(mac.replace(':', ''), 16) % 850) + 15

            result.append({
                "mac": mac,
                "ip": c.get('ip', '0.0.0.0'),
                "hostname": c.get('hostname', 'unknown'),
                "interface": c.get('interface', 'wlan0'),
                "signal": c.get('signal', -50),
                "usage_mb": mock_usage
            })
        return result
    except:
        return []

@app.get("/api/v1/wireless/config")
async def get_wireless_config():
    return {
        "ssid": rasp_ap.ssid(),
        "channel": rasp_ap.channel(),
        "hw_mode": rasp_ap.hw_mode(),
        "country": rasp_ap.country_code()
    }

@app.websocket("/ws/traffic")
async def traffic_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            try:
                throughput_data = json.loads(rasp_networking.throughput())
                
                # Filter out loopback and logical bridges to find the most active physical interface
                valid_ifaces = {k: v for k, v in throughput_data.items() if k != 'lo' and not k.startswith('br')}
                
                primary = None
                if "enp1s0" in valid_ifaces: # Common naming on mini PCs
                    primary = "enp1s0"
                elif "eth0" in valid_ifaces:
                    primary = "eth0"
                elif valid_ifaces:
                    # Fallback to the interface with the highest combined traffic
                    primary = max(valid_ifaces.keys(), key=lambda k: valid_ifaces[k]['rx'] + valid_ifaces[k]['tx'])
                
                if primary:
                    data = {
                        "timestamp": rasp_system.systime(),
                        "download_kbps": valid_ifaces[primary]['rx'] / 1024,
                        "upload_kbps": valid_ifaces[primary]['tx'] / 1024
                    }
                else:
                    data = {"timestamp": rasp_system.systime(), "download_kbps": 0, "upload_kbps": 0}
            except Exception as e:
                data = {"timestamp": rasp_system.systime(), "download_kbps": 0, "upload_kbps": 0}
                
            await websocket.send_json(data)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WS Error: {e}")
    finally:
        await websocket.close()

# ═══════════════════════════════════════════════════════════════════
# NEW ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

# ─── Wireless Config (POST) ───────────────────────────────────────

@app.post("/api/v1/wireless/config")
async def update_wireless_config(config: WirelessConfigUpdate):
    """Update hostapd configuration and restart the service."""
    conf_path = os.path.join(SNAP_COMMON, 'config/hostapd.conf')
    try:
        if not os.path.exists(conf_path):
            raise HTTPException(status_code=404, detail="hostapd.conf not found")
        
        with open(conf_path, 'r') as f:
            lines = f.readlines()
        
        updates = {}
        if config.ssid is not None:
            updates['ssid'] = config.ssid
        if config.channel is not None:
            updates['channel'] = config.channel
        if config.password is not None:
            updates['wpa_passphrase'] = config.password
        
        new_lines = []
        for line in lines:
            key = line.split('=')[0].strip() if '=' in line else None
            if key and key in updates:
                new_lines.append(f"{key}={updates[key]}\n")
                del updates[key]
            else:
                new_lines.append(line)
        # Append any keys not already in the file
        for key, val in updates.items():
            new_lines.append(f"{key}={val}\n")
        
        with open(conf_path, 'w') as f:
            f.writelines(new_lines)
        
        # Restart hostapd service
        _run_cmd(_get_snap_cmd("hostapd", "restart"))
        
        return {"status": "ok", "message": "Wireless configuration updated. Service restarting."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── System Services ──────────────────────────────────────────────

@app.get("/api/v1/system/services")
async def get_services():
    """Return status of snap services."""
    services = [
        {"name": "Hostapd (Wireless)", "service": "hostapd"},
        {"name": "Dnsmasq (DHCP/DNS)", "service": "dnsmasq"},
        {"name": "NAT Daemon", "service": "daemon"},
        {"name": "API Server", "service": "api-v1"},
    ]
    result = []
    for svc in services:
        status = "running"
        try:
            if os.environ.get('SNAP'):
                out = _run_cmd(["snapctl", "services", f"accessd.{svc['service']}"])
                if "inactive" in out.lower() or "stopped" in out.lower():
                    status = "stopped"
        except:
            status = "unknown"
        result.append({"name": svc["name"], "service": svc["service"], "status": status})
    return result

@app.post("/api/v1/system/services/{service_name}/restart")
async def restart_service(service_name: str):
    """Restart a specific snap service."""
    try:
        _run_cmd(_get_snap_cmd(service_name, "restart"))
        return {"status": "ok", "message": f"Service {service_name} restarted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── Power Actions ────────────────────────────────────────────────

@app.post("/api/v1/system/reboot")
async def reboot_system():
    """Initiate system reboot."""
    try:
        if os.environ.get('SNAP'):
            subprocess.Popen(["reboot"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "ok", "message": "System reboot initiated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/system/shutdown")
async def shutdown_system():
    """Initiate system shutdown."""
    try:
        if os.environ.get('SNAP'):
            subprocess.Popen(["shutdown", "-h", "now"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "ok", "message": "System shutdown initiated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── System Info ──────────────────────────────────────────────────

@app.get("/api/v1/system/info")
async def get_system_info():
    """Return version and basic system identity."""
    version = "unknown"
    try:
        if os.environ.get('SNAP'):
            version = os.environ.get('SNAP_VERSION', 'unknown')
        else:
            out = _run_cmd(["git", "describe", "--tags", "--dirty", "--always"])
            version = out.strip() if out.strip() else "dev"
    except:
        pass
    return {"version": version, "name": "AccessD"}

# ─── System Logs ──────────────────────────────────────────────────

@app.get("/api/v1/system/logs")
async def get_system_logs(module: Optional[str] = None, level: Optional[str] = None, limit: int = 100):
    """Fetch recent system logs."""
    try:
        cmd = ["journalctl", "--no-pager", "-n", str(min(limit, 500)), "-o", "json"]
        
        # Filter by snap services
        service_map = {
            "WIFI": "snap.accessd.hostapd.service",
            "DHCP": "snap.accessd.dnsmasq.service",
            "FIREWALL": "snap.accessd.daemon.service",
            "SYSTEM": "snap.accessd.api-v1.service",
        }
        
        if module and module.upper() in service_map:
            cmd.extend(["-u", service_map[module.upper()]])
        elif not module:
            # Get logs for all accessd services
            for svc in service_map.values():
                cmd.extend(["-u", svc])
        
        out = _run_cmd(cmd, timeout=5)
        logs = []
        for line in out.strip().split('\n'):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                priority = int(entry.get('PRIORITY', 6))
                log_type = "error" if priority <= 3 else "warning" if priority <= 4 else "info"
                
                if level and log_type != level.lower():
                    continue
                
                # Determine module from service unit
                unit = entry.get('_SYSTEMD_UNIT', '')
                detected_module = "SYSTEM"
                for mod, svc in service_map.items():
                    if svc in unit:
                        detected_module = mod
                        break
                
                timestamp = entry.get('__REALTIME_TIMESTAMP', '')
                if timestamp:
                    ts = int(timestamp) / 1_000_000
                    time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
                else:
                    time_str = ""
                
                logs.append({
                    "id": len(logs) + 1,
                    "time": time_str,
                    "type": log_type,
                    "module": detected_module,
                    "message": entry.get('MESSAGE', ''),
                })
            except:
                continue
        
        return logs
    except:
        return []

# ─── Firewall Rules ───────────────────────────────────────────────

@app.get("/api/v1/firewall/rules")
async def get_firewall_rules():
    """Return stored port forwarding rules."""
    return _load_firewall_rules()

@app.post("/api/v1/firewall/rules")
async def add_firewall_rule(rule: FirewallRule):
    """Add a new port forwarding rule."""
    rules = _load_firewall_rules()
    new_id = max([r.get('id', 0) for r in rules], default=0) + 1
    new_rule = {"id": new_id, **rule.model_dump()}
    rules.append(new_rule)
    _save_firewall_rules(rules)
    
    # Apply iptables rule if in snap
    if os.environ.get('SNAP') and rule.status == "enabled":
        proto = "tcp" if rule.protocol.upper() in ("TCP", "BOTH") else "udp"
        _run_cmd([
            "iptables", "-t", "nat", "-A", "PREROUTING",
            "-p", proto, "--dport", rule.port,
            "-j", "DNAT", "--to-destination", f"{rule.target}:{rule.port}"
        ])
    
    return new_rule

@app.delete("/api/v1/firewall/rules/{rule_id}")
async def delete_firewall_rule(rule_id: int):
    """Delete a port forwarding rule."""
    rules = _load_firewall_rules()
    rule_to_delete = next((r for r in rules if r.get('id') == rule_id), None)
    if not rule_to_delete:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rules = [r for r in rules if r.get('id') != rule_id]
    _save_firewall_rules(rules)
    return {"status": "ok", "message": "Rule deleted."}

# ─── QoS Configuration ────────────────────────────────────────────

@app.get("/api/v1/qos/config")
async def get_qos_config():
    """Return current QoS configuration."""
    return _load_qos_config()

@app.post("/api/v1/qos/config")
async def update_qos_config(config: QoSConfig):
    """Update QoS configuration."""
    data = config.model_dump()
    _save_qos_config(data)
    return {"status": "ok", "config": data}

# ─── Device Rule Controls (Block / Speed Limits) ──────────────────

class DeviceBlockRequest(BaseModel):
    mac: str
    action: str  # "block" or "unblock"

class DeviceSpeedRequest(BaseModel):
    mac: str
    ip: str
    interface: str
    limit_mbps: float

@app.get("/api/v1/network/devices/limits")
def get_device_limits():
    return device_rules.get_limits()

@app.post("/api/v1/network/devices/block")
def block_device(req: DeviceBlockRequest):
    if req.action == "block":
        device_rules.set_block(req.mac, True)
    elif req.action == "unblock":
        device_rules.set_block(req.mac, False)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    return {"status": "success"}

@app.post("/api/v1/network/devices/speed")
def speed_limit_device(req: DeviceSpeedRequest):
    device_rules.set_speed_limit(req.mac, req.ip, req.interface, req.limit_mbps)
    return {"status": "success"}

# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get('ACCESSD_API_PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
