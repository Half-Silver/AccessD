# Quick Start Guide

## 1. Build the Snap

```bash
sudo snap install snapcraft --classic
cd wifi-router-snap
snapcraft
```

## 2. Install on Ubuntu Core

```bash
# Transfer to your device
scp accessd_*.snap user@device:~

# Install
sudo snap install --dangerous accessd_*.snap

# Connect interfaces
sudo snap connect accessd:firewall-control
sudo snap connect accessd:network-control
sudo snap connect accessd:network-setup-control
```

## 3. Configure

```bash
# Check your network interfaces
ip link show

# Configure WiFi
sudo accessd.configure \
  --ssid "MyNetwork" \
  --password "MySecurePass123" \
  --wan-interface eth0 \
  --lan-interface wlan0
```

## 4. Start

```bash
# Restart to apply configuration
sudo snap restart accessd

# Check status
accessd.status
```

## 5. Connect

Connect your devices to the WiFi network using the SSID and password you configured!

## Common Commands

```bash
# View configuration
accessd.configure --show

# Check status
accessd.status

# View logs
sudo snap logs accessd -f

# Restart
sudo snap restart accessd
```
