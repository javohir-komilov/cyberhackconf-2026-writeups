<?php
// Tizim xavfsizlik devori (Naive WAF simulation)
$raw_input = $_SERVER['REQUEST_URI'] . file_get_contents('php://input');
$waf_blocked = ['allow_url_include', 'auto_prepend_file', 'php://', 'data://'];

foreach ($waf_blocked as $blocked) {
    if (strpos($raw_input, $blocked) !== false) {
        http_response_code(403);
        die("WAF: Xavfli so'rov aniqlandi! Tizim himoyalangan.");
    }
}

// PHPRC yordamida eski rejimni taqlid qilish (Legacy mode simulation)
if (isset($_GET['PHPRC']) && $_GET['PHPRC'] === '/dev/fd/0') {
    parse_str(file_get_contents('php://input'), $legacy_configs);
    
    if (isset($legacy_configs['auto_prepend_file'])) {
        $file_to_include = $legacy_configs['auto_prepend_file'];
        
        // Tizim ichki fayllariga xavfsiz o'qish imkoniyati (Controlled read)
        if (file_exists($file_to_include) && strpos($file_to_include, '../') === false) {
            echo "<!-- Xabar: Eski rejim faollashtirildi. Fayl biriktirilmoqda... -->\n";
            readfile($file_to_include);
        }
    }
}
?>
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <title>Tizim Haqida - TransGlobe Freight Solutions</title>
    <link rel="stylesheet" href="assets/style.css">
</head>
<body>
    <div class="header">
        <h1>TransGlobe Freight Solutions</h1>
        <p>Ichki Logistika Boshqaruv Tizimi</p>
    </div>
    
    <table width="100%" height="500px" border="0" cellpadding="0" cellspacing="0" class="main-layout">
        <tr>
            <td valign="top" width="200px" class="sidebar">
                <ul>
                    <li><a href="index.php">Bosh sahifa</a></li>
                    <li><a href="dashboard.php">Boshqaruv paneli</a></li>
                    <li><a href="info.php">Tizim haqida</a></li>
                    <li><a href="health.php">Holat tekshiruvi</a></li>
                </ul>
            </td>
            <td valign="top" class="content">
                <h2>Tizim haqida (System Info)</h2>
                <p>TransGlobe Freight Solutions kompaniyasining logistika va yuklarni boshqarishga mo'ljallangan yopiq tizimi.</p>
                <table class="data-table">
                    <tr>
                        <th width="30%">Versiya</th>
                        <td>v1.0.4-legacy (2012 Reliz)</td>
                    </tr>
                    <tr>
                        <th>Muallif</th>
                        <td>TransGlobe IT bo'limi</td>
                    </tr>
                    <tr>
                        <th>Platforma</th>
                        <td>Apache &amp; PHP-CGI texnologiyalari</td>
                    </tr>
                    <tr>
                        <th>So'nggi yangilanish</th>
                        <td>Noyabr 2012-yil</td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>

    <div class="footer">
        &copy; 2012 TransGlobe Freight Solutions. Barcha huquqlar himoyalangan.
    </div>
</body>
</html>
