# AccessD Backend API (v1)

The AccessD backend is a FastAPI-based server that provides real-time status and configuration endpoints for the WiFi router. It serves as a bridge between the Web UI and the underlying Linux system tools.

## Architecture

- **Server**: FastAPI with Uvicorn
- **Language**: Python 3
- **Modules**: Located in `scripts/api/modules/`
  - `system.py`: CPU, memory, uptime, and temperature
  - `ap.py`: Wireless configuration (hostapd)
  - `client.py`: Connected devices (dnsmasq leases)
  - `networking.py`: Interface status and throughput

## Base URL

When running as a snap, the API is available locally at:
`http://localhost:8000/api/v1`

(The port can be configured via the `ACCESSD_API_PORT` environment variable).

## Endpoints

### 1. System Stats
**Endpoint:** `GET /api/v1/system/stats`

**Description:** Returns current CPU usage, memory consumption, uptime, and system temperature.

**Response Example:**
```json
{
  "cpu": {
    "usage": 18.5,
    "model": "Raspberry Pi 4 Model B Rev 1.4",
    "load_avg": [0.8, 0.5, 0.4]
  },
  "memory": {
    "used_pct": 32.1,
    "total_gb": 4.0,
    "used_gb": 1.28
  },
  "uptime": "12:45:30",
  "temp": 45.2
}
```

### 2. Network Interfaces
**Endpoint:** `GET /api/v1/network/interfaces`

**Description:** Lists available network interfaces and their current status.

**Response Example:**
```json
[
  {
    "name": "eth0",
    "type": "WAN",
    "status": "up",
    "ip": "172.16.0.45",
    "mask": "255.255.255.0"
  },
  {
    "name": "wlan0",
    "type": "LAN",
    "status": "up",
    "ip": "192.168.50.1",
    "mask": "255.255.255.0"
  }
]
```

### 3. Connected Clients
**Endpoint:** `GET /api/v1/network/clients`

**Description:** Retrieves a list of currently connected devices from the DHCP leases.

**Response Example:**
```json
[
  {
    "mac": "DE:AD:BE:EF:CA:FE",
    "ip": "192.168.50.102",
    "hostname": "MacBook-Pro",
    "interface": "wlan0",
    "signal": -42,
    "usage_mb": 0
  }
]
```

### 4. Wireless Configuration
**Endpoint:** `GET /api/v1/wireless/config`

**Description:** Returns current hostapd configuration (SSID, channel, etc.).

**Response Example:**
```json
{
  "ssid": "AccessD-WiFi",
  "channel": "6",
  "hw_mode": "g",
  "country": "US"
}
```

## Real-time Traffic (WebSocket)

**Endpoint:** `WS /ws/traffic`

**Description:** Provides a streaming JSON message every 1 second with current throughput statistics.

**Message Format:**
```json
{
  "timestamp": "14:02:11",
  "download_kbps": 842.1,
  "upload_kbps": 145.2
}
```

## Deployment & Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ACCESSD_API_PORT` | Port the API server listens on | `8000` |
| `SNAP` | Snap root directory (if running in snap) | `.` |
| `SNAP_COMMON` | Snap common data directory | `/var/snap/accessd/common` |

### Running Locally

To run the API server for development:

```bash
export ACCESSD_API_PORT=8000
python3 scripts/api-server.py
```

*Note: If running on a non-Linux system, the server will use mock modules automatically.*

## Internal Modules Reference (`scripts/api/modules/`)

### `system.py`
- `uptime()`: Returns uptime string.
- `systemLoadPercentage()`: Calculates CPU load.
- `usedMemory()`: Returns memory usage percentage.
- `systemTemperature()`: Reads from `/sys/class/thermal/`.
- `rpiRevision()`: Identifies the device model.

### `ap.py`
- `ssid()`, `channel()`, `hw_mode()`, `country_code()`: Parse `hostapd.conf`.

### `client.py`
- `get_active_clients()`: Parses `dnsmasq.leases`.

### `networking.py`
- `interfaces()`: Parses `/proc/net/dev`.
- `throughput()`: Calculates delta of RX/TX bytes over time.
