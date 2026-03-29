<?php

if (session_status() === PHP_SESSION_NONE && !headers_sent()) {
    @session_start();
}

if (isset($_SESSION) && !isset($_SESSION['lastActivity'])) {
    $_SESSION['lastActivity'] = time();
}

