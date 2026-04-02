# AccessD Architecture

AccessD is designed as a modern, snap-packaged router management system. It consists of three primary layers: the Linux kernel/system services, the Python-based API, and the Next.js Web UI.

## Overview

```mermaid
graph TD
    UI[Next.js Web UI] <--> API[FastAPI Backend]
    API <--> Modules[Python System Modules]
    Modules <--> Proc[/proc & /sys FS]
    Modules <--> Config[Config Files: hostapd.conf, etc.]
    Modules <--> Leases[DHCP Leases: dnsmasq.leases]
    
    SubGraph[System Daemons]
    Modules -.-> Status[accessd.status script]
    hostapd[hostapd daemon]
    dnsmasq[dnsmasq daemon]
    nat[nat-daemon script]
```

## Components

### 1. System Daemons (Lower Layer)
The core routing functionality is provided by standard Linux tools:
- **hostapd**: Manages the WiFi access point.
- **dnsmasq**: Provides DHCP and DNS services.
- **iptables**: Configures NAT and firewall rules.
- **nat-daemon**: A script that ensures IP forwarding and NAT rules are consistently applied.

### 2. Backend API (Middle Layer)
The backend (`scripts/api-server.py`) is a FastAPI application that:
- Periodically reads system status from `/proc` and `/sys`.
- Parses configuration files to provide a structured view of the router.
- Provides a WebSocket for real-time traffic monitoring.
- Is packaged as the `api-v1` app in the snap.

### 3. Web UI (Upper Layer)
The management interface (`external/accessd.web/`) is a Next.js application:
- Built with TailwindCSS and Shadcn UI.
- Communicates with the Backend API for all data.
- Optimized for mobile and desktop screens.

## Data Flow

### Status Monitoring
1. The Web UI connects to the Backend API via HTTP (REST) and WebSockets.
2. The Backend API uses internal Python modules to read system state.
3. Modules read directly from the kernel filesystem (`/proc/net/dev`, `/proc/loadavg`, etc.) to minimize overhead.

### Configuration Changes
1. (In Progress) The Web UI sends configuration updates to the Backend API.
2. The Backend API updates the relevant configuration files (e.g., `hostapd.conf`).
3. The Backend API triggers a reload/restart of the affected system service (e.g., `snap restart accessd.hostapd`).

## Snap Integration

AccessD is packaged as a strictly confined snap, which ensures:
- **Security**: Isolation from the host system's sensitive files.
- **Reliability**: Atomic updates and easy rollbacks.
- **Dependencies**: All required tools (hostapd, dnsmasq, iptables) are bundled within the snap.

### Key Interfaces (Plugs)
- `network`: Basic network access.
- `network-bind`: Ability to listen on ports (80, 8080, 8000).
- `network-control`: Ability to manage network interfaces.
- `firewall-control`: Ability to set iptables rules.
- `network-setup-control`: Advanced network configuration.

## Further Reading
- [Backend API Specification (v1)](./BACKEND_API.md)
- [System Mapping (UI to Linux Commands)](../external/accessd.web/docs/SYSTEM_MAPPING.md)
