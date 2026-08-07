from playwright.sync_api import Page


def get_offer_cards(page: Page):
    """
    Returns all visible vehicle offer cards.
    """

    selectors = [
        ".vehicle-card",
        ".offer-card",
        ".card",
        "[data-testid='vehicle-card']",
    ]

    for selector in selectors:
        cards = page.locator(selector)

        try:
            count = cards.count()

            if count > 0:
                print(f"✅ Found {count} cards using '{selector}'")
                return cards

        except Exception:
            pass

    print("❌ No offer cards found")
    return None