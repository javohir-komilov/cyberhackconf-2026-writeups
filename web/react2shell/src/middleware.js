import { NextResponse } from 'next/server';

// ┌─────────────────────────────────────────────────────┐
// │          SECURESHIELD WAF v2.1.4                    │
// │   Enterprise Web Application Firewall               │
// │   Powered by TechMart Security Division             │
// └─────────────────────────────────────────────────────┘

const WAF_VERSION = '2.1.4';
const WAF_PRODUCT = 'SecureShield';

// Blocked patterns - covers known attack vectors
const BLOCKED_PATTERNS = [
  { regex: /constructor/i,    rule: 'SS-001', desc: 'Prototype chain traversal' },
  { regex: /\beval\b/i,       rule: 'SS-002', desc: 'Dynamic code evaluation' },
  { regex: /child_process/i,  rule: 'SS-003', desc: 'Process spawning module' },
  { regex: /require\s*\(/i,   rule: 'SS-004', desc: 'Module loading' },
  { regex: /execSync/i,       rule: 'SS-005', desc: 'Synchronous execution' },
  { regex: /execFile/i,       rule: 'SS-006', desc: 'File execution' },
  { regex: /spawnSync/i,      rule: 'SS-007', desc: 'Synchronous spawn' },
  { regex: /__proto__/i,      rule: 'SS-008', desc: 'Prototype access' },
  { regex: /prototype\s*\[/i, rule: 'SS-009', desc: 'Prototype property access' },
  { regex: /mainModule/i,     rule: 'SS-010', desc: 'Module tree traversal' },
  { regex: /readFileSync/i,   rule: 'SS-011', desc: 'Synchronous file read' },
  { regex: /writeFileSync/i,  rule: 'SS-012', desc: 'Synchronous file write' },
  { regex: /process\s*\./i,   rule: 'SS-013', desc: 'Process object access' },
  { regex: /global\s*\[/i,    rule: 'SS-014', desc: 'Global namespace access' },
  { regex: /binding\s*\(/i,   rule: 'SS-015', desc: 'Native binding access' },
  { regex: /openSync\s*\(/i,  rule: 'SS-016', desc: 'Synchronous file open' },
  { regex: /Buffer\s*\./i,    rule: 'SS-017', desc: 'Buffer object access' },
  { regex: /vm\s*\.\s*run/i,  rule: 'SS-018', desc: 'VM execution context' },
  { regex: /Function\s*\(/i,  rule: 'SS-019', desc: 'Function constructor call' },
  { regex: /import\s*\(/i,    rule: 'SS-020', desc: 'Dynamic import' },
];

// Valid next-action header must be exactly 40 lowercase hex chars
const ACTION_ID_REGEX = /^[0-9a-f]{40}$/;

function wafBlockPage(rule, desc, ref) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>403 - ${WAF_PRODUCT} WAF | Access Denied</title>
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{background:#030305;color:#f0f0f8;font-family:'Courier New',monospace;
         min-height:100vh;display:flex;align-items:center;justify-content:center}
    .container{max-width:680px;width:90%;padding:20px}
    .badge{display:inline-block;background:#ff2d78;color:#fff;font-size:10px;
           font-weight:700;letter-spacing:2px;padding:4px 10px;margin-bottom:20px;
           text-transform:uppercase}
    .box{border:1px solid #1a1a2e;background:#080810;padding:28px 32px;
         border-left:3px solid #ff2d78}
    pre.ascii{color:#ff2d78;font-size:11px;line-height:1.4;margin-bottom:20px;
              opacity:0.8}
    h1{font-size:28px;color:#ff2d78;letter-spacing:3px;margin-bottom:6px;
       text-transform:uppercase}
    .subtitle{color:#606078;font-size:12px;letter-spacing:2px;margin-bottom:24px}
    .divider{border:none;border-top:1px solid #1a1a2e;margin:20px 0}
    .row{display:flex;justify-content:space-between;padding:8px 0;
         border-bottom:1px solid #0d0d18;font-size:13px}
    .row .label{color:#606078;text-transform:uppercase;letter-spacing:1px;font-size:11px}
    .row .value{color:#a0a0b8}
    .row .value.red{color:#ff2d78}
    .footer{margin-top:24px;font-size:11px;color:#303048;text-align:center;
            letter-spacing:1px}
    .blink{animation:blink 1s step-end infinite}
    @keyframes blink{50%{opacity:0}}
  </style>
</head>
<body>
  <div class="container">
    <span class="badge">${WAF_PRODUCT} WAF</span>
    <div class="box">
      <pre class="ascii">╔═══════════════════════════════════════════╗
║  ██╗    ██╗ █████╗ ███████╗               ║
║  ██║    ██║██╔══██╗██╔════╝               ║
║  ██║ █╗ ██║███████║█████╗                 ║
║  ██║███╗██║██╔══██║██╔══╝                 ║
║  ╚███╔███╔╝██║  ██║██║    <span class="blink">▌</span>              ║
║   ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝                   ║
╚═══════════════════════════════════════════╝</pre>
      <h1>Access Denied</h1>
      <p class="subtitle">Request blocked by ${WAF_PRODUCT} WAF v${WAF_VERSION}</p>
      <hr class="divider">
      <div class="row">
        <span class="label">Status</span>
        <span class="value red">403 FORBIDDEN</span>
      </div>
      <div class="row">
        <span class="label">Rule ID</span>
        <span class="value">${rule}</span>
      </div>
      <div class="row">
        <span class="label">Reason</span>
        <span class="value">${desc}</span>
      </div>
      <div class="row">
        <span class="label">Reference</span>
        <span class="value">${ref}</span>
      </div>
      <div class="row">
        <span class="label">Action</span>
        <span class="value red">BLOCK &amp; LOG</span>
      </div>
      <hr class="divider">
      <p class="footer">
        This incident has been logged and reported.<br>
        If you believe this is an error, contact security@techmart.local
      </p>
    </div>
  </div>
</body>
</html>`;
}

export async function middleware(request) {
  const { pathname, searchParams } = request.nextUrl;
  const nextAction = request.headers.get('next-action');

  // WAF only inspects Server Action requests
  if (!nextAction) {
    return NextResponse.next();
  }

  // Generate incident reference
  const ref = `WAF-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).substr(2, 6).toUpperCase()}`;

  // Rule: Validate next-action header format
  if (!ACTION_ID_REGEX.test(nextAction)) {
    return new NextResponse(
      wafBlockPage('SS-000', 'Invalid action identifier format', ref),
      {
        status: 403,
        headers: {
          'Content-Type': 'text/html',
          'X-WAF-Version': WAF_VERSION,
          'X-WAF-Rule': 'SS-000',
          'X-WAF-Ref': ref,
        },
      }
    );
  }

  // Rule: Validate Content-Type for Server Actions
  const contentType = request.headers.get('content-type') || '';
  const allowedTypes = ['text/plain', 'multipart/form-data', 'application/x-www-form-urlencoded'];
  if (!allowedTypes.some((t) => contentType.toLowerCase().includes(t))) {
    return new NextResponse(
      wafBlockPage('SS-CT', 'Disallowed content-type for server action', ref),
      {
        status: 403,
        headers: {
          'Content-Type': 'text/html',
          'X-WAF-Version': WAF_VERSION,
          'X-WAF-Rule': 'SS-CT',
          'X-WAF-Ref': ref,
        },
      }
    );
  }

  // Rule: Body size limit (64KB)
  const contentLength = parseInt(request.headers.get('content-length') || '0');
  if (contentLength > 65536) {
    return new NextResponse(
      wafBlockPage('SS-SZ', 'Request body exceeds allowed size', ref),
      {
        status: 413,
        headers: {
          'Content-Type': 'text/html',
          'X-WAF-Version': WAF_VERSION,
          'X-WAF-Rule': 'SS-SZ',
          'X-WAF-Ref': ref,
        },
      }
    );
  }

  // Rule: Deep pattern inspection on raw body
  try {
    const cloned = request.clone();
    const rawBody = await cloned.text();

    // Size check on actual body
    if (rawBody.length > 65536) {
      return new NextResponse(
        wafBlockPage('SS-SZ', 'Request body exceeds allowed size', ref),
        { status: 413, headers: { 'Content-Type': 'text/html', 'X-WAF-Version': WAF_VERSION } }
      );
    }

    // Pattern matching on RAW body (no decoding performed)
    for (const { regex, rule, desc } of BLOCKED_PATTERNS) {
      if (regex.test(rawBody)) {
        return new NextResponse(
          wafBlockPage(rule, desc, ref),
          {
            status: 403,
            headers: {
              'Content-Type': 'text/html',
              'X-WAF-Version': WAF_VERSION,
              'X-WAF-Rule': rule,
              'X-WAF-Ref': ref,
            },
          }
        );
      }
    }
  } catch {
    return new NextResponse(
      wafBlockPage('SS-ERR', 'Request inspection failure', ref),
      { status: 403, headers: { 'Content-Type': 'text/html' } }
    );
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon\\.ico).*)'],
};
