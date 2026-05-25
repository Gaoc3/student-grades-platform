from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()

    # Test RTL
    page = browser.new_page()
    page.goto('http://127.0.0.1:5000/dashboard')
    page.evaluate("document.documentElement.setAttribute('dir', 'rtl')")
    page.evaluate("document.documentElement.setAttribute('lang', 'ar')")
    page.screenshot(path='rtl_dashboard.png')

    # Test LTR
    page.evaluate("document.documentElement.setAttribute('dir', 'ltr')")
    page.evaluate("document.documentElement.setAttribute('lang', 'en')")
    page.screenshot(path='ltr_dashboard.png')

    browser.close()
