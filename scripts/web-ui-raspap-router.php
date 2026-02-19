<?php

$configuredWebroot = getenv('ACCESSD_WEBROOT');
if ($configuredWebroot !== false && $configuredWebroot !== '') {
    $webroot = realpath($configuredWebroot);
} else {
    $webroot = realpath(__DIR__ . '/../external/accessd.webui');
}

if ($webroot === false) {
    http_response_code(500);
    echo "Missing web root";
    exit;
}

// Make relative include paths behave like lighttpd document-root execution.
chdir($webroot);
$_SERVER['DOCUMENT_ROOT'] = $webroot;

$uriPath = urldecode(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH) ?? '/');
$candidate = realpath($webroot . $uriPath);

if ($candidate !== false && strpos($candidate, $webroot) === 0 && is_file($candidate)) {
    return false;
}

$pathInfo = $uriPath;
if ($pathInfo === '/index.php') {
    $pathInfo = '/';
}

$_SERVER['PATH_INFO'] = ($pathInfo === '/') ? '' : $pathInfo;
$_SERVER['SCRIPT_NAME'] = '/index.php';
$_SERVER['PHP_SELF'] = '/index.php' . $_SERVER['PATH_INFO'];

require $webroot . '/index.php';
