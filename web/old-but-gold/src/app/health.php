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
    <title>Holat Tekshiruvi - TransGlobe Freight Solutions</title>
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
                <h2>Holat tekshiruvi (Health Check)</h2>
                <p>Barcha xizmatlar barqaror ishlamoqda.</p>
                <table class="data-table">
                    <tr>
                        <th>Xizmat nomi</th>
                        <th>Holati</th>
                    </tr>
                    <tr>
                        <td>Ma'lumotlar bazasi aloqasi</td>
                        <td style="color: green; font-weight: bold;">Ulangan v. MySQL 5.1</td>
                    </tr>
                    <tr>
                        <td>Fayl tizimi yozish huquqi</td>
                        <td style="color: green; font-weight: bold;">Faol / Tekshirilgan</td>
                    </tr>
                    <tr>
                        <td>Xavfsizlik moduli (WAF)</td>
                        <td style="color: green; font-weight: bold;">Cheklovlar yoqilgan</td>
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
