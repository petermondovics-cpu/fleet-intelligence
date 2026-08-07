from playwright.sync_api import Page


def accept_cookies(page: Page) -> bool:
    """
    Accept the cookie banner if it is displayed.
    Returns True if a button was clicked, otherwise False.
    """

    selectors = [
        "button#onetrust-accept-btn-handler",
        "button:has-text('Elfogadom')",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Accept')",
    ]

    for selector in selectors:
        try:
            button = page.locator(selector).first
            if button.is_visible(timeout=2000):
                button.click()
                print("🍪 Cookie banner accepted")
                return True
        except Exception:
            pass

    print("ℹ️ No cookie banner found")
    return False