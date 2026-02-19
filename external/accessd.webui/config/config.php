<?php

if (!function_exists('accessd_env')) {
    function accessd_env(string $name, string $default): string
    {
        $value = getenv($name);
        if ($value === false || $value === '') {
            return $default;
        }
        return $value;
    }
}

// Fallbacks for environments where ext-ctype is not available.
if (!function_exists('ctype_digit')) {
    function ctype_digit($text): bool
    {
        $value = (string) $text;
        return $value !== '' && preg_match('/^[0-9]+$/', $value) === 1;
    }
}

if (!function_exists('ctype_xdigit')) {
    function ctype_xdigit($text): bool
    {
        $value = (string) $text;
        return $value !== '' && preg_match('/^[A-Fa-f0-9]+$/', $value) === 1;
    }
}

if (!function_exists('ctype_print')) {
    function ctype_print($text): bool
    {
        $value = (string) $text;
        return $value !== '' && preg_match('/^[\x20-\x7E]+$/', $value) === 1;
    }
}

define('RASPI_BRAND_TEXT', 'AccessD');
define('RASPI_BRAND_TITLE', RASPI_BRAND_TEXT.' Admin Panel');
define('RASPI_CONFIG', accessd_env('ACCESSD_RASPI_CONFIG', '/etc/accessd'));
define('RASPI_CONFIG_NETWORK', accessd_env('ACCESSD_RASPI_CONFIG_NETWORK', RASPI_CONFIG.'/networking/defaults.json'));
define('RASPI_CONFIG_PROVIDERS', accessd_env('ACCESSD_RASPI_CONFIG_PROVIDERS', 'config/vpn-providers.json'));
define('RASPI_CONFIG_API', accessd_env('ACCESSD_RASPI_CONFIG_API', RASPI_CONFIG.'/api'));
define('RASPI_ADMIN_DETAILS', accessd_env('ACCESSD_RASPI_ADMIN_DETAILS', RASPI_CONFIG.'/accessd.auth'));
define('RASPI_WIFI_AP_INTERFACE', accessd_env('ACCESSD_RASPI_WIFI_AP_INTERFACE', 'wlan0'));
define('RASPI_CACHE_PATH', accessd_env('ACCESSD_RASPI_CACHE_PATH', sys_get_temp_dir() . '/accessd'));
define('RASPI_ERROR_LOG', accessd_env('ACCESSD_RASPI_ERROR_LOG', sys_get_temp_dir() . '/accessd_error.log'));
define('RASPI_DEBUG_LOG', accessd_env('ACCESSD_RASPI_DEBUG_LOG', 'accessd_debug.log'));
define('RASPI_LOG_SIZE_LIMIT', 64);
define('RASPI_SESSION_TIMEOUT', 1440);

// Constants for configuration file paths.
// These are typical for default RPi installs. Modify if needed.
define('RASPI_DNSMASQ_LEASES', accessd_env('ACCESSD_RASPI_DNSMASQ_LEASES', '/var/lib/misc/dnsmasq.leases'));
define('RASPI_DNSMASQ_PREFIX', accessd_env('ACCESSD_RASPI_DNSMASQ_PREFIX', '/etc/dnsmasq.d/090_'));
define('RASPI_ADBLOCK_LISTPATH', accessd_env('ACCESSD_RASPI_ADBLOCK_LISTPATH', '/etc/accessd/adblock/'));
define('RASPI_ADBLOCK_CONFIG', accessd_env('ACCESSD_RASPI_ADBLOCK_CONFIG', RASPI_DNSMASQ_PREFIX.'adblock.conf'));
define('RASPI_HOSTAPD_CONFIG', accessd_env('ACCESSD_RASPI_HOSTAPD_CONFIG', '/etc/hostapd/hostapd.conf'));
define('RASPI_DHCPCD_CONFIG', accessd_env('ACCESSD_RASPI_DHCPCD_CONFIG', '/etc/dhcpcd.conf'));
define('RASPI_DHCPCD_LOG', accessd_env('ACCESSD_RASPI_DHCPCD_LOG', '/var/log/dnsmasq.log'));
define('RASPI_WPA_SUPPLICANT_CONFIG', accessd_env('ACCESSD_RASPI_WPA_SUPPLICANT_CONFIG', '/etc/wpa_supplicant/wpa_supplicant.conf'));
define('RASPI_HOSTAPD_CTRL_INTERFACE', accessd_env('ACCESSD_RASPI_HOSTAPD_CTRL_INTERFACE', '/var/run/hostapd'));
define('RASPI_WPA_CTRL_INTERFACE', accessd_env('ACCESSD_RASPI_WPA_CTRL_INTERFACE', '/var/run/wpa_supplicant'));
define('RASPI_OPENVPN_CLIENT_PATH', accessd_env('ACCESSD_RASPI_OPENVPN_CLIENT_PATH', '/etc/openvpn/client/'));
define('RASPI_OPENVPN_CLIENT_CONFIG', accessd_env('ACCESSD_RASPI_OPENVPN_CLIENT_CONFIG', '/etc/openvpn/client/client.conf'));
define('RASPI_OPENVPN_CLIENT_LOGIN', accessd_env('ACCESSD_RASPI_OPENVPN_CLIENT_LOGIN', '/etc/openvpn/client/login.conf'));
define('RASPI_WIREGUARD_PATH', accessd_env('ACCESSD_RASPI_WIREGUARD_PATH', '/etc/wireguard/'));
define('RASPI_WIREGUARD_CONFIG', RASPI_WIREGUARD_PATH.'wg0.conf');
define('RASPI_IPTABLES_CONF', accessd_env('ACCESSD_RASPI_IPTABLES_CONF', RASPI_CONFIG.'/networking/iptables_rules.json'));
define('RASPI_TORPROXY_CONFIG', accessd_env('ACCESSD_RASPI_TORPROXY_CONFIG', '/etc/tor/torrc'));
define('RASPI_LIGHTTPD_CONFIG', accessd_env('ACCESSD_RASPI_LIGHTTPD_CONFIG', '/etc/lighttpd/lighttpd.conf'));
define('RASPI_ACCESS_CHECK_IP', '1.1.1.1');
define('RASPI_ACCESS_CHECK_DNS', 'one.one.one.one');

// Constant for the GitHub API latest release endpoint
define('RASPI_API_ENDPOINT', 'https://api.github.com/repos/AccessD/accessd-webui/releases/latest');

// Captive portal detection - returns 204 or 200 is successful
define('RASPI_ACCESS_CHECK_URL', 'http://detectportal.firefox.com');
define('RASPI_ACCESS_CHECK_URL_CODE', 200);

// Constant for the 5GHz wireless regulatory domain
define("RASPI_5GHZ_CHANNEL_MIN", 100);
define("RASPI_5GHZ_CHANNEL_MAX", 192);

// Enable basic authentication for the web admin.
define('RASPI_AUTH_ENABLED', true);

// Optional services, set to true to enable.
define('RASPI_WIFICLIENT_ENABLED', true);
define('RASPI_HOTSPOT_ENABLED', true);
define('RASPI_NETWORK_ENABLED', true);
define('RASPI_DHCP_ENABLED', true);
define('RASPI_ADBLOCK_ENABLED', false);
define('RASPI_OPENVPN_ENABLED', false);
define('RASPI_VPN_PROVIDER_ENABLED', false);
define('RASPI_WIREGUARD_ENABLED', false);
define('RASPI_TORPROXY_ENABLED', false);
define('RASPI_CONFAUTH_ENABLED', true);
define('RASPI_CHANGETHEME_ENABLED', true);
define('RASPI_VNSTAT_ENABLED', true);
define('RASPI_SYSTEM_ENABLED', true);
define('RASPI_MONITOR_ENABLED', false);
define('RASPI_RESTAPI_ENABLED', false);
define('RASPI_PLUGINS_ENABLED', true);
define('RASPI_UI_STATIC_LOGO', false);

// Locale settings
define('LOCALE_ROOT', 'locale');
define('LOCALE_DOMAIN', 'messages');
