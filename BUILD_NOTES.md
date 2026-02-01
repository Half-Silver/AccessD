# Build Notes and Fixes

## Recent Updates (Fixed Issues)

### Build Errors Fixed:
1. **Execute Permissions**: Added `chmod +x` in the scripts part to ensure all scripts are executable
2. **Plug Warnings**: Removed global plugs section - plugs are now properly assigned to each app
3. **Missing Metadata**: Added `title`, `license`, and `contact` fields to snapcraft.yaml
4. **Library Dependency**: Added `libatm1` package to resolve library linter warning

## Building the Snap

### Prerequisites
```bash
sudo snap install snapcraft --classic
```

### Build Command
```bash
cd accessd-snap
snapcraft pack --destructive-mode
```

Or for a clean build in a container:
```bash
snapcraft --use-lxd
```

### Expected Output
- The build should complete without permission errors
- You'll get a file like: `accessd_1.0_amd64.snap`
- Some lint warnings about optional metadata fields are normal

## Installation

```bash
# Install the snap
sudo snap install --dangerous accessd_*.snap

# Connect required interfaces
sudo snap connect accessd:firewall-control
sudo snap connect accessd:network-control
sudo snap connect accessd:network-setup-control
```

## Troubleshooting Build Issues

### GLIBC Warnings During Linting
The GLIBC warnings you see during the linting phase are normal when building in destructive mode on a newer system. They don't affect the final snap package - it will work correctly on Ubuntu Core 22.

### Permission Errors
If you still get permission errors, ensure:
1. Your scripts in the `scripts/` directory exist
2. The snapcraft.yaml has the `chmod +x` line in the scripts part override-build

### Build in Clean Environment
For the most reliable build, use LXD:
```bash
sudo snap install lxd
sudo lxd init --auto
snapcraft --use-lxd
```

This avoids any host system compatibility issues.
