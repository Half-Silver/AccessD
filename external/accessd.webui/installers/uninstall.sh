#!/bin/bash
#
# AccessD uninstall functions
# Author: @billz <billzimmerman@gmail.com>
# License: GNU General Public License v3.0
#
# You are not obligated to bundle the LICENSE file with your AccessD projects as long
# as you leave these references intact in the header comments of your source files.

# Exit on error
set -o errexit
# Exit on error inside functions
set -o errtrace
# Turn on traces, disabled by default
# set -o xtrace

# Set defaults
readonly accessd_dir="/etc/accessd"
readonly accessd_user="www-data"
readonly accessd_sudoers="/etc/sudoers.d/090_accessd"
readonly accessd_default="/etc/dnsmasq.d/090_accessd.conf"
readonly accessd_wlan0="/etc/dnsmasq.d/090_wlan0.conf"
readonly accessd_sysctl="/etc/sysctl.d/90_accessd.conf"
readonly accessd_adblock="/etc/dnsmasq.d/090_adblock.conf"
readonly accessd_network="/etc/systemd/network/"
readonly rulesv4="/etc/iptables/rules.v4"
webroot_dir="/var/www/html"

# Determines host Linux distribution details
function _get_linux_distro() {
    if type lsb_release >/dev/null 2>&1; then # linuxbase.org
        OS=$(lsb_release -si)
        RELEASE=$(lsb_release -sr)
        CODENAME=$(lsb_release -sc)
        DESC=$(lsb_release -sd)
        LONG_BIT=$(getconf LONG_BIT)
    elif [ -f /etc/os-release ]; then # freedesktop.org
        . /etc/os-release
        OS=$ID
        RELEASE=$VERSION_ID
        CODENAME=$VERSION_CODENAME
        DESC=$PRETTY_NAME
    else
        _install_error "Unsupported Linux distribution"
    fi
}

# Sets php package option based on Linux version, abort if unsupported distro
function _set_php_package() {
    case $RELEASE in
        13) # Debian 13 trixie
            php_package="php8.4-fpm"
            phpiniconf="/etc/php/8.4/fpm/php.ini" ;;
        23.05|12*) # Debian 12 & Armbian 23.05
            php_package="php8.2-cgi"
            phpiniconf="/etc/php/8.2/cgi/php.ini" ;;
        23.04) # Ubuntu Server 23.04
            php_package="php8.1-cgi"
            phpiniconf="/etc/php/8.1/cgi/php.ini" ;;
        22.04|20.04|18.04|19.10|11*) # Previous Ubuntu Server, Debian & Armbian distros
            php_package="php7.4-cgi"
            phpiniconf="/etc/php/7.4/cgi/php.ini" ;;
        10*|11*)
            php_package="php7.3-cgi"
            phpiniconf="/etc/php/7.3/cgi/php.ini" ;;
        9*)
            php_package="php7.0-cgi"
            phpiniconf="/etc/php/7.0/cgi/php.ini" ;;
        8)
            _install_error "${DESC} and php5 are unsupported."
            exit 1 ;;
        *)
            _install_error "${DESC} is unsupported."
            exit 1 ;;
    esac
}

# Outputs a AccessD Install log line
function _install_log() {
    echo -e "\033[1;32mAccessD Uninstall: $*\033[m"
}

# Outputs a AccessD Install Error log line and exits with status code 1
function _install_error() {
    echo -e "\033[1;37;41mAccessD Uninstall Error: $*\033[m"
    exit 1
}

# Checks to make sure uninstallation info is correct
function _config_uninstallation() {
    _install_log "Configure uninstall of AccessD"
    _get_linux_distro
    echo "Detected OS: ${DESC} ${LONG_BIT}-bit"
    echo "AccessD install directory: ${accessd_dir}"
    echo -n "Lighttpd install directory: ${webroot_dir}? [Y/n]: "
    read answer
    if [ "$answer" != "${answer#[Nn]}" ]; then
        read -e -p "Enter alternate lighttpd directory: " -i "/var/www/html" webroot_dir
    fi
    echo "Uninstall from lighttpd directory: ${webroot_dir}"
    echo -n "Uninstall AccessD with these values? [Y/n]: "
    read answer
    if [[ "$answer" != "${answer#[Nn]}" ]]; then
        echo "Installation aborted."
        exit 0
    fi
}

# Checks for/restore backup files
function _check_for_backups() {
    if [ -d "$accessd_dir/backups" ]; then
        if [ -f "$accessd_dir/backups/hostapd.conf" ]; then
            echo -n "Restore the last hostapd configuration file? [y/N]: "
            read answer
            if [[ $answer -eq 'y' ]]; then
                sudo cp "$accessd_dir/backups/hostapd.conf" /etc/hostapd/hostapd.conf
            fi
        fi
        if [ -f "$accessd_dir/backups/dnsmasq.conf" ]; then
            echo -n "Restore the last dnsmasq configuration file? [y/N]: "
            read answer
            if [[ $answer -eq 'y' ]]; then
                sudo cp "$accessd_dir/backups/dnsmasq.conf" /etc/dnsmasq.conf
            fi
        fi
        if [ -f "$accessd_dir/backups/dhcpcd.conf" ]; then
            echo -n "Restore the last dhcpcd.conf file? [y/N]: "
            read answer
            if [[ $answer -eq 'y' ]]; then
                sudo cp "$accessd_dir/backups/dhcpcd.conf" /etc/dhcpcd.conf
            fi
        fi
        if [ -f "$accessd_dir/backups/php.ini" ] && [ -f "$phpiniconf" ]; then
            echo -n "Restore the last php.ini file? [y/N]: "
            read answer
            if [[ $answer -eq 'y' ]]; then
                sudo cp "$accessd_dir/backups/php.ini" "$phpiniconf"
            fi
        fi
    fi
}

# Removes AccessD directories
function _remove_accessd_directories() {
    _install_log "Removing AccessD Directories"
    if [ ! -d "$accessd_dir" ]; then
        _install_error "AccessD Configuration directory not found. Exiting."
    fi

    if [ ! -d "$webroot_dir" ]; then
        _install_error "AccessD Installation directory not found. Exiting."
    fi
    sudo rm -rf "$webroot_dir"/* || _install_error "Unable to remove $webroot_dir"
    sudo rm -rf "$accessd_dir" || _install_error "Unable to remove $accessd_dir"
}

# Removes accessdd.service
function _remove_accessd_service() {
    _install_log "Removing accessdd.service"
    if [ -f /lib/systemd/system/accessdd.service ]; then
        sudo rm /lib/systemd/system/accessdd.service || _install_error "Unable to remove accessd.service file"
    fi
    sudo systemctl daemon-reload
    echo "Done."
}

# Restores networking config to pre-install defaults
function _restore_networking() {
    _install_log "Restoring networking config to pre-install defaults"
    echo "Disabling IP forwarding in $accessd_sysctl"
    sudo rm "$accessd_sysctl" || _install_error "Unable to remove $accessd_sysctl"
    sudo /etc/init.d/procps restart || _install_error "Unable to execute procps"
    echo "Checking iptables rules"
    rules=(
    "-A POSTROUTING -j MASQUERADE"
    "-A POSTROUTING -s 192.168.50.0/24 ! -d 192.168.50.0/24 -j MASQUERADE"
    )
    for rule in "${rules[@]}"; do
        if grep -- "$rule" $rulesv4 > /dev/null; then
            rule=$(sed -e 's/^\(-A POSTROUTING\)/-t nat -D POSTROUTING/' <<< $rule)
            echo "Removing rule: ${rule}"
            sudo iptables $rule || _install_error "Unable to execute iptables"
            removed=true
        fi
    done
    # Persist rules if removed
    if [ "$removed" = true ]; then
        echo "Removing persistent iptables rules"
        sudo iptables-save | sudo tee $rulesv4 > /dev/null || _install_error "Unable to execute iptables-save"
    fi
    echo "Done."
    # Remove dnsmasq and bridge configs
    echo "Removing 090_accessd.conf from dnsmasq"
    if [ -f $accessd_default ]; then
        sudo rm "$accessd_default" || _install_error "Unable to remove $accessd_default"
    fi
    echo "Removing 090_wlan0.conf from dnsmasq"
    if [ -f $accessd_wlan0 ]; then
        sudo rm "$accessd_wlan0" || _install_error "Unable to remove $accessd_wlan0"
    fi
    echo "Removing accessd bridge configurations"
    sudo rm "$accessd_network"/accessd* || _install_error "Unable to remove bridge config"
    if [ -f $accessd_adblock ]; then
        echo "Removing accessd adblock configuration"
        sudo rm "$accessd_adblock" || _install_error "Unable to remove adblock config"
    fi
}

# Removes installed packages
function _remove_installed_packages() {
    _install_log "Removing installed packages"
    _set_php_package

    # Set default
    dhcpcd_package="dnsmasq"

    if [ ${OS,,} = "debian" ] || [ ${OS,,} = "ubuntu" ]; then
        dhcpcd_package="dhcpcd5"
        iw_package="iw"
    fi
    if [ ${OS,,} = "raspbian" ] && [[ ${RELEASE} =~ ^(12) ]]; then
        dhcpcd_package="dhcpcd dhcpcd-base"
    fi

    echo -n "Remove the following installed packages? lighttpd hostapd iptables-persistent $php_package $dhcpcd_package $iw_package vnstat qrencode jq [y/N]: "
    read answer
    if [ "$answer" == 'y' ] || [ "$answer" == 'Y' ]; then
        echo "Removing packages."
        sudo apt-get remove lighttpd hostapd iptables-persistent $php_package $dhcpcd_package $iw_package vnstat qrencode jq || _install_error "Unable to remove installed packages"
        sudo apt-get autoremove || _install_error "Unable to run apt autoremove"
    else
        echo "Leaving packages installed."
    fi
}

# Removes www-data from sudoers
function _remove_sudoers() {
    _install_log "Removing sudoers permissions"
    echo "Removing ${accessd_sudoers}" 
    sudo rm "$accessd_sudoers" || _install_error "Unable to remove $accessd_sudoers"
    echo "Done."
}

function _remove_lighttpd_config() {
    echo "Unlinking 50-accessd-router.conf from /etc/lighttpd/conf-enabled/"
    sudo unlink "/etc/lighttpd/conf-enabled/50-accessd-router.conf" || _install_error "Unable to unlink lighttpd config"
    echo "Removing 50-accessd-router.conf from /etc/lighttpd/conf-available/"
    sudo rm "/etc/lighttpd/conf-available/50-accessd-router.conf" || _install_error "Unable to remove lighttpd config"
    sudo systemctl restart lighttpd.service || _install_status 1 "Unable to restart lighttpd"
    echo "Done."
}

function _uninstall_complete() {
    _install_log "Uninstall completed"
    echo "Check your network configuration before rebooting to ensure access."
}

function _remove_accessd() {
    _config_uninstallation
    _check_for_backups
    _remove_accessd_service
    _restore_networking
    _remove_accessd_directories
    _remove_lighttpd_config
    _remove_installed_packages
    _remove_sudoers
    _uninstall_complete
}

