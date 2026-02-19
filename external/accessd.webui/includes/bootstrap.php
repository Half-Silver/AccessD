<?php
// cache-control headers
if (!headers_sent()) {
    header("Cache-Control: no-store, no-cache, must-revalidate");
    header("Pragma: no-cache");
    header("Expires: 0");
}

// Fallback i18n helpers for environments where ext-gettext isn't available.
if (!function_exists('_')) {
    function _($message)
    {
        return $message;
    }
}

if (!function_exists('ngettext')) {
    function ngettext($singular, $plural, $count)
    {
        return ((int) $count === 1) ? $singular : $plural;
    }
}
