from playwright.sync_api import sync_playwright

def bypass_cloudflare(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=10000)
            page.wait_for_load_state('networkidle', timeout=15000)
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        print(f"Cloudflare bypass failed: {e}")
        return None
