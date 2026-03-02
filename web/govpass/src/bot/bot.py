"""
GovPass Security Review Bot
============================
Logs in as admin, polls for pending vulnerability reports,
and visits each report's PoC URL in a sandboxed browser session.
"""
import os
import time
import requests
from playwright.sync_api import sync_playwright

PORTAL_URL = os.environ.get("PORTAL_URL", "http://web:5000").rstrip("/")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "20"))
BOT_VISIT_TIMEOUT = 300_000  # ms — stay on PoC page long enough for full flag leak (~5 min)


def get_admin_session() -> requests.Session:
    """Return a requests.Session authenticated as admin (for API calls)."""
    s = requests.Session()
    resp = s.post(f"{PORTAL_URL}/auth/login", data={
        "username": "admin",
        "password": ADMIN_PASSWORD,
    }, allow_redirects=False)
    if resp.status_code not in (200, 302):
        raise RuntimeError(f"Admin login failed: {resp.status_code}")
    return s


def fetch_pending_reports(api_session: requests.Session) -> list:
    resp = api_session.get(f"{PORTAL_URL}/admin/api/reports/pending")
    if resp.status_code != 200:
        return []
    return resp.json()


def mark_visited(api_session: requests.Session, report_id: int):
    api_session.post(f"{PORTAL_URL}/admin/api/reports/{report_id}/visited")


def visit_poc(poc_url: str, cookies: list):
    """Open poc_url in a headless Chromium session carrying the admin cookies."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
        ])
        ctx = browser.new_context()
        # Inject admin session cookies so the browser is authenticated
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        try:
            page.goto(poc_url, timeout=15_000, wait_until="domcontentloaded")
            # Wait long enough for any async XS-Leak exfiltration to complete
            page.wait_for_timeout(BOT_VISIT_TIMEOUT)
        except Exception as exc:
            print(f"[bot] Error visiting {poc_url}: {exc}")
        finally:
            browser.close()


def get_playwright_cookies(api_session: requests.Session) -> list:
    """Convert requests.Session cookies to Playwright cookie format."""
    cookies = []
    for name, value in api_session.cookies.items():
        cookies.append({
            "name": name,
            "value": value,
            "domain": PORTAL_URL.split("://", 1)[1].split("/")[0].split(":")[0],
            "path": "/",
        })
    return cookies


def run():
    print(f"[bot] Starting. Portal: {PORTAL_URL}  Poll interval: {POLL_INTERVAL}s")
    # Wait for web service to be ready
    for attempt in range(30):
        try:
            r = requests.get(f"{PORTAL_URL}/", timeout=3)
            if r.status_code < 500:
                break
        except Exception:
            pass
        print(f"[bot] Waiting for portal... ({attempt+1}/30)")
        time.sleep(3)

    while True:
        try:
            api_session = get_admin_session()
            reports = fetch_pending_reports(api_session)
            if reports:
                print(f"[bot] {len(reports)} pending report(s) to review.")
            cookies = get_playwright_cookies(api_session)
            for report in reports:
                poc_url = report.get("poc_url", "")
                rid = report.get("id")
                print(f"[bot] Visiting report #{rid}: {poc_url}")
                visit_poc(poc_url, cookies)
                mark_visited(api_session, rid)
                print(f"[bot] Done with report #{rid}.")
        except Exception as exc:
            print(f"[bot] Cycle error: {exc}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()
