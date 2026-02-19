<?php header("Content-Type: text/css; charset=utf-8"); ?>
<?php
require_once '../../includes/functions.php';
$color = getColorOpt();
$allCss = 'all.css';
?>
/*
Theme Name: AccessD default
Author: @billz
Author URI: https://github.com/billz
Description: Default theme for AccessD
License: GNU General Public License v3.0
*/

@import url('<?= $allCss ?>?v=<?= filemtime($allCss); ?>');

:root {
  --accessd-theme-color: <?php echo htmlspecialchars($color, ENT_QUOTES, 'UTF-8'); ?>;
  --accessd-theme-lighter: <?php echo htmlspecialchars(lightenColor($color, 20), ENT_QUOTES, 'UTF-8'); ?>;
  --accessd-theme-darker: <?php echo htmlspecialchars(darkenColor($color, 20), ENT_QUOTES, 'UTF-8'); ?>;
}

body {
  color: #212529;
  background-color: #f8f9fc;
}

a {
  color: var(--accessd-theme-color);
  text-decoration: none;
}

a:focus, a:hover {
  color: var(--accessd-theme-darker);
}

.sb-sidenav-light .sb-sidenav-menu .nav-link:hover {
  color: var(--accessd-theme-color);
}

.sidebar-brand-text:focus,
.sidebar-brand-text:hover {
  color: var(--accessd-theme-darker);
}

.form-check-input:checked {
  background-color: var(--accessd-theme-color); 
  border-color: var(--accessd-theme-color); 
}

.sidebar {
  background-color: #f8f9fc;
}

.sb-nav-link-icon.active {
  font-weight: 600;
}

.sidebar .nav-item.active .nav-link {
  font-weight: 500;
}

.sidebar-brand-text {
  color: var(--accessd-theme-color); 
}

.card .card-header, .modal-header {
  border-color: var(--accessd-theme-color); 
  color: #fff;
  background-color: var(--accessd-theme-color); 
}

.modal-header {
  border-radius: 0px;
}

.btn-primary {
  color: var(--accessd-theme-color); 
  border-color: var(--accessd-theme-color); 
  background-color: #fff;
}

.btn-primary:disabled {
  color: var(--accessd-theme-color) !important;
  border-color: var(--accessd-theme-color) !important;
  background-color: #fff !important;
}

.card-body {
  color: #495057;
}

.card-footer, .modal-footer {
  background-color: #f2f1f0;
}

.nav-tabs .nav-link.active,
.nav-tabs .nav-link {
  font-size: 1.0rem;
}

.nav-tabs a.nav-link {
  color: #6e707e;
}

a.nav-link.active {
  font-weight: bolder;
}

.sidebar .nav-item .nav-link {
  padding: 0.6rem 0.6rem 0.6rem 1.0rem;
}

.btn-primary {
  background-color: #fff;
}

.btn-warning {
  color: #333;
}

.btn-primary:hover {
  background-color: var(--accessd-theme-color); 
  border-color: var(--accessd-theme-color); 
}

i.fa.fa-bars {
  color: #d1d3e2;
}

i.fa.fa-bars:hover{
  color: #6e707e;
}

pre.unstyled {
  border-width: 0;
  background-color: transparent;
  padding: 0;
}

.sidebar.toggled .nav-item .nav-link span {
  display: none;
} .sidebar .nav-item .nav-link i,
.sidebar .nav-item .nav-link span {
    font-size: 1.0rem;
}

.btn-warning:hover {
    color: #000;
}

.signal-icon .signal-bar {
  background: var(--accessd-theme-color); 
}

