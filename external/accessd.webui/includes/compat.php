<?php

/**
 * AccessD Snap compatibility layer
 */

if (!function_exists('accessd_sync_router_conf')) {
    function accessd_sync_router_conf(string $fileName)
    {
        $router_conf = getenv('ACCESSD_RASPI_ROUTER_CONF');
        if (!$router_conf) {
            $snap_common = getenv('SNAP_COMMON');
            if ($snap_common) {
                $router_conf = "$snap_common/config/router.conf";
            } else {
                // fallback for local dev
                $root_dir = realpath(__DIR__ . '/../../');
                $router_conf = "$root_dir/.dev/snap-common/config/router.conf";
            }
        }

        if (!file_exists($router_conf)) {
            return;
        }

        // Only sync if it's one of the files we care about
        $sync_needed = false;
        $file_basename = basename($fileName);
        if (in_array($file_basename, ['hostapd.conf', 'dnsmasq.conf', 'router.conf'])) {
            $sync_needed = true;
        }

        if (!$sync_needed) {
            return;
        }

        // Load existing router.conf
        $config = [];
        if (file_exists($router_conf)) {
            $lines = file($router_conf, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
            foreach ($lines as $line) {
                if (strpos($line, '=') !== false && strpos($line, '#') !== 0) {
                    list($key, $value) = explode('=', $line, 2);
                    $value = trim($value, '"\'');
                    $config[$key] = $value;
                }
            }
        }

        // Update from hostapd.conf if changed
        $hostapd_conf = defined('RASPI_HOSTAPD_CONFIG') ? RASPI_HOSTAPD_CONFIG : null;
        if ($hostapd_conf && file_exists($hostapd_conf)) {
            $h_lines = file($hostapd_conf, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
            foreach ($h_lines as $line) {
                if (strpos($line, '=') !== false && strpos($line, '#') !== 0) {
                    list($key, $value) = explode('=', $line, 2);
                    $value = trim($value);
                    switch ($key) {
                        case 'ssid':
                            $config['SSID'] = $value;
                            break;
                        case 'wpa_passphrase':
                            $config['WPA_PASSPHRASE'] = $value;
                            break;
                        case 'channel':
                            $config['CHANNEL'] = $value;
                            break;
                        case 'interface':
                            $config['LAN_INTERFACE'] = $value;
                            break;
                    }
                }
            }
        }

        // Update from dnsmasq.conf
        $dnsmasq_prefix = defined('RASPI_DNSMASQ_PREFIX') ? RASPI_DNSMASQ_PREFIX : null;
        if ($dnsmasq_prefix) {
            $dnsmasq_conf = $dnsmasq_prefix . (getenv('ACCESSD_AP_INTERFACE') ?: 'wlan0') . '.conf';
            // Check if the specific interface config exists, otherwise check the prefix as a file (some versions use it)
            if (!file_exists($dnsmasq_conf) && file_exists($dnsmasq_prefix)) {
                 $dnsmasq_conf = $dnsmasq_prefix;
            }
            
            if (file_exists($dnsmasq_conf)) {
                $d_lines = file($dnsmasq_conf, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
                foreach ($d_lines as $line) {
                    if (strpos($line, 'dhcp-range=') === 0) {
                        $range = substr($line, 11);
                        $parts = explode(',', $range);
                        if (count($parts) >= 2) {
                            $config['DHCP_START'] = $parts[0];
                            $config['DHCP_END'] = $parts[1];
                            if (isset($parts[2]) && strpos($parts[2], '.') !== false) {
                                $config['LAN_NETMASK'] = $parts[2];
                            }
                            if (isset($parts[3])) {
                                $config['DHCP_LEASE'] = $parts[3];
                            }
                        }
                    }
                }
            }
        }

        // Write back to router.conf
        $out = "# Updated by AccessD WebUI Compatibility Layer\n";
        foreach ($config as $key => $value) {
            $out .= "$key=" . escapeshellarg($value) . "\n";
        }
        file_put_contents($router_conf, $out);

        // Notify snap to restart if running in a snap
        if (getenv('SNAP')) {
            @exec('snapctl restart accessd.hostapd accessd.dnsmasq 2>/dev/null');
        }
    }
}

if (!function_exists('accessd_exec_wrapper')) {
    function accessd_exec_wrapper($command, &$output = null, &$result_code = null)
    {
        // Strip sudo
        $command = preg_replace('/^sudo\s+/', '', $command);
        $command = preg_replace('/\s+sudo\s+/', ' ', $command);

        // Redirect systemctl to snapctl if appropriate
        if (strpos($command, 'systemctl') !== false) {
             $command = preg_replace('/systemctl\s+restart\s+hostapd(\.service)?/', 'snapctl restart accessd.hostapd', $command);
             $command = preg_replace('/systemctl\s+stop\s+hostapd(\.service)?/', 'snapctl stop accessd.hostapd', $command);
             $command = preg_replace('/systemctl\s+start\s+hostapd(\.service)?/', 'snapctl start accessd.hostapd', $command);

             $command = preg_replace('/systemctl\s+restart\s+dnsmasq(\.service)?/', 'snapctl restart accessd.dnsmasq', $command);
             $command = preg_replace('/systemctl\s+stop\s+dnsmasq(\.service)?/', 'snapctl stop accessd.dnsmasq', $command);
             $command = preg_replace('/systemctl\s+start\s+dnsmasq(\.service)?/', 'snapctl start accessd.dnsmasq', $command);

             if (strpos($command, 'systemctl') !== false) {
                 $command = str_replace('systemctl', 'snapctl', $command);
             }
        }

        $snap = getenv('SNAP');
        if ($snap) {
            $command = str_replace('/etc/accessd/hostapd/servicestart.sh', "$snap/bin/servicestart.sh", $command);
            $command = str_replace('/etc/accessd/lighttpd/configport.sh', "$snap/bin/configport.sh", $command);
        }

        return exec($command, $output, $result_code);
    }
}
