#!/usr/bin/env python3
import os
import sys
import json
import asyncio
import subprocess
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List

# Add the vendored RaspAP modules to path
SNAP = os.environ.get('SNAP', '.')
API_PATH = os.path.join(SNAP, 'external/accessd.webui/api')
if os.path.exists(API_PATH):
    sys.path.append(API_PATH)

try:
    import modules.system as rasp_system
    import modules.ap as rasp_ap
    import modules.client as rasp_client
    import modules.networking as rasp_networking
except ImportError:
    # Mock modules for local development if not found
    print("Warning: RaspAP modules not found, using mock data")
    class MockModule:
        def __getattr__(self, name):
            return lambda *args, **kwargs: {}
    rasp_system = rasp_ap = rasp_client = rasp_networking = MockModule()

app = FastAPI(title="AccessD API v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/system/stats")
async def get_system_stats():
    return {
        "cpu": {
            "usage": rasp_system.systemLoadPercentage(),
            "model": rasp_system.rpiRevision(),
            "load_avg": [rasp_system.LoadAvg1Min(), 0.5, 0.4] # Mocking 5/15 min for now
        },
        "memory": {
            "used_pct": rasp_system.usedMemory(),
            "total_gb": 4.0, # Placeholder, can be improved
            "used_gb": (rasp_system.usedMemory() / 100.0) * 4.0
        },
        "uptime": rasp_system.uptime(),
        "temp": rasp_system.systemTemperature()
    }

@app.get("/api/v1/network/interfaces")
async def get_interfaces():
    try:
        ifaces = json.loads(rasp_networking.interfaces())
        # Transform to expected format
        result = []
        for iface in ifaces:
            result.append({
                "name": iface.get('interface', 'unknown'),
                "type": "WAN" if iface.get('interface') == "eth0" else "LAN",
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
            result.append({
                "mac": c.get('mac', '00:00:00:00:00:00'),
                "ip": c.get('ip', '0.0.0.0'),
                "hostname": c.get('hostname', 'unknown'),
                "interface": c.get('interface', 'wlan0'),
                "signal": c.get('signal', -50),
                "usage_mb": 0 # Not provided by RaspAP module directly
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
            # Get throughput from rasp_networking
            try:
                # throughput() returns a JSON string with interfaces as keys
                # and 'rx'/'tx' as subkeys (bps)
                throughput_data = json.loads(rasp_networking.throughput())
                # Default to eth0 or wlan0 for dashboard summary
                primary = "eth0" if "eth0" in throughput_data else list(throughput_data.keys())[0] if throughput_data else None
                
                if primary:
                    data = {
                        "timestamp": rasp_system.systime(),
                        "download_kbps": throughput_data[primary]['rx'] / 1024,
                        "upload_kbps": throughput_data[primary]['tx'] / 1024
                    }
                else:
                    data = {"download_kbps": 0, "upload_kbps": 0}
            except:
                data = {"download_kbps": 0, "upload_kbps": 0}
                
            await websocket.send_json(data)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WS Error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get('ACCESSD_API_PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
