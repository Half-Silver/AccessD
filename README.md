# Accessd - WiFi Router Snap for Ubuntu Core

Turn your mini PC into a WiFi router with this Ubuntu Core snap package.

## Features

- **WiFi Access Point**: Create a WiFi network using hostapd
- **DHCP Server**: Automatic IP assignment with dnsmasq
- **DNS Server**: Built-in DNS forwarding
- **NAT Routing**: Share internet connection from WAN to WiFi clients
- **Easy Configuration**: Simple command-line configuration tool
- **Status Monitoring**: Check router status and connected clients
- **Web Management UI**: Browser-based router dashboard on port 8080
- **Parental Controls**: Per-device internet blocking (always-on or scheduled)

## Prerequisites

- Ubuntu Core system or Ubuntu with snapd installed
- Mini PC with at least two network interfaces:
  - One for WAN (internet connection) - typically eth0
  - One WiFi adapter for LAN (access point) - typically wlan0
- WiFi adapter that supports AP mode (check with `iw list`)

## Building the Snap

```bash
# Install snapcraft if not already installed
sudo snap install snapcraft --classic

# Build the snap
cd wifi-router-snap
snapcraft

# This will create a .snap file (e.g., accessd_1.0_amd64.snap)
```

## Installation

### On Ubuntu Core

```bash
# Copy the snap to your Ubuntu Core device
scp accessd_*.snap user@ubuntu-core-device:~

# SSH into the device
ssh user@ubuntu-core-device

# Install the snap
sudo snap install --dangerous accessd_*.snap

# Connect required interfaces
sudo snap connect accessd:firewall-control
sudo snap connect accessd:network-control
sudo snap connect accessd:network-setup-control
sudo snap connect accessd:network-bind
```

### On Regular Ubuntu

```bash
# Install the snap
sudo snap install --dangerous accessd_*.snap

# Connect required interfaces
sudo snap connect accessd:firewall-control
sudo snap connect accessd:network-control
sudo snap connect accessd:network-setup-control
sudo snap connect accessd:network-bind
```

## Configuration

### Initial Setup

Before starting the router, configure your network settings:

```bash
# Set WiFi network name and password
sudo accessd.configure --ssid "MyWiFiNetwork" --password "SecurePassword123"

# Set WiFi channel (optional, default is 6)
sudo accessd.configure --channel 11

# Configure network interfaces (if different from defaults)
sudo accessd.configure --wan-interface eth0 --lan-interface wlan0

# Set custom LAN IP and DHCP range (optional)
sudo accessd.configure --lan-ip 192.168.1.1 \
  --dhcp-start 192.168.1.100 \
  --dhcp-end 192.168.1.200
```

### View Current Configuration

```bash
accessd.configure --show
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--ssid` | WiFi network name | WiFiRouter |
| `--password` | WiFi password (min 8 chars) | changeme123 |
| `--channel` | WiFi channel (1-13) | 6 |
| `--wan-interface` | Internet-facing interface | eth0 |
| `--lan-interface` | WiFi interface | wlan0 |
| `--lan-ip` | Router IP address | 192.168.50.1 |
| `--dhcp-start` | DHCP range start | 192.168.50.100 |
| `--dhcp-end` | DHCP range end | 192.168.50.200 |

## Usage

### Start the Router

```bash
# The daemon starts automatically after installation
# To restart after configuration changes:
sudo snap restart accessd
```

### Open Web UI

Once installed, the management interface is available at:

```text
http://<router-ip>:8080
```

Default login:

- Username: `admin`
- Password: current WiFi password from `router.conf` (or `admin12345` fallback)

Use the web console to:

- Update SSID, password, channel, and interface settings
- View connected DHCP clients
- Create parental control rules by MAC address
- Apply always-on or time-based internet blocking

### Check Status

```bash
accessd.status
```

This will show:
- Current configuration
- Network interface status
- Running services (hostapd, dnsmasq)
- IP forwarding and NAT status
- Connected clients

### Stop the Router

```bash
sudo snap stop accessd
```

### View Logs

```bash
sudo snap logs accessd -f
```

## Troubleshooting

### WiFi adapter not found

Check available wireless interfaces:
```bash
ip link show
iw dev
```

### WiFi adapter doesn't support AP mode

Check capabilities:
```bash
iw list | grep "Supported interface modes" -A 8
```

Look for `AP` in the list.

### Router not forwarding traffic

Check IP forwarding:
```bash
cat /proc/sys/net/ipv4/ip_forward
```

Check NAT rules:
```bash
sudo iptables -t nat -L -n -v
```

### WiFi blocked by rfkill

```bash
sudo rfkill unblock wifi
```

### Can't connect to WiFi

1. Check if hostapd is running: `accessd.status`
2. Check logs: `sudo snap logs accessd`
3. Verify password is at least 8 characters
4. Try a different channel

### No internet on connected devices

1. Verify WAN interface has internet: `ping -I eth0 8.8.8.8`
2. Check NAT rules: `sudo iptables -t nat -L -n`
3. Verify IP forwarding is enabled
4. Check DNS: `accessd.configure --show`

## Network Diagram

```
Internet
   |
   | (WAN Interface - eth0)
   |
[Mini PC Router]
   |
   | (LAN Interface - wlan0)
   |
WiFi Clients (192.168.50.100-200)
```

## Security Notes

- **Change the default password**: The default password "changeme123" is not secure
- **Use WPA2**: The snap uses WPA2-PSK encryption by default
- **Firewall**: Consider adding additional iptables rules for security
- **Updates**: Keep the snap and Ubuntu Core updated

## Advanced Configuration

### Custom iptables Rules

The snap sets up basic NAT. For custom firewall rules, you can add them after the router starts:

```bash
# Example: Block specific ports
sudo iptables -A FORWARD -p tcp --dport 25 -j DROP
```

### Performance Tuning

For better performance with many clients, you can adjust hostapd settings by modifying the configuration in:
```
/var/snap/accessd/common/config/hostapd.conf
```

Then restart: `sudo snap restart accessd`

## Uninstallation

```bash
sudo snap remove accessd
```

## Development

### Local Web UI Preview (npm)

You can run the RaspAP-based management UI directly during development without building a snap:

```bash
npm run webui
```

This runs the vendored UI from `external/accessd.webui/`.
You can also call it explicitly:

```bash
npm run webui:raspap
```

Notes:
- `webui:raspap` requires `php` on your machine.
- It serves on `http://127.0.0.1:8090` by default.
- Default login (when no `accessd.auth` exists): `admin` / `secret`.

Or bind only to localhost:

```bash
npm run webui:local
```

Then open:

```text
http://127.0.0.1:8090
```

For local preview, runtime data is stored in `.dev/snap-common/`.

### Local Web UI Service (npm, no Docker)

Run the UI in the background and manage it like a local service:

```bash
# Start service
npm run webui:service:start

# Start service on localhost explicitly
npm run webui:service:start:local

# Check service status
npm run webui:service:status

# View recent logs
npm run webui:service:logs

# Follow logs live
npm run webui:service:logs:follow

# Restart / stop
npm run webui:service:restart
npm run webui:service:stop
```

Preview URL (localhost mode):

```text
http://localhost:8090
```

### File Structure

```
wifi-router-snap/
├── snapcraft.yaml          # Snap manifest
├── scripts/
│   ├── router-daemon       # Main router daemon
│   ├── configure           # Configuration tool
│   └── status              # Status monitoring
└── README.md               # This file
```

### Contributing

Feel free to modify and improve this snap for your specific needs!

## License

This snap configuration is provided as-is for educational and practical use.

## Support

For issues specific to:
- hostapd: See hostapd documentation
- dnsmasq: See dnsmasq documentation
- Ubuntu Core: See Ubuntu Core documentation
- Snap packaging: See snapcraft.io documentation
