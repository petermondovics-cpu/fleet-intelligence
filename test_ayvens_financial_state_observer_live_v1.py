from playwright.sync_api import sync_playwright

from scrapers.ayvens.financial_state_observer import (
    AyvensFinancialStateObserver,
)


URL = "https://autotartosberlet.ayvens.com/byd/atto-2-dm-i"


def dismiss(page):
    for selector in (
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
    ):
        loc = page.locator(selector)

        if not loc.count():
            continue

        try:
            loc.first.click(timeout=1800)
            page.wait_for_timeout(300)
            return
        except Exception:
            pass


def main():
    print("=" * 88)
    print("AYVENS FINANCIAL STATE OBSERVER LIVE V1")
    print("=" * 88)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        page.goto(
            URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(2200)
        dismiss(page)

        result = (
            AyvensFinancialStateObserver()
            .observe(page)
        )

        on = result.with_initial_payment
        off = result.without_initial_payment

        print("\n--- SWITCH ON ---")
        print("aria-checked:", on.switch_checked)
        print(
            "Down payment:",
            f"{on.down_payment_percent:.0f}%",
        )
        print(
            "Monthly fee:",
            f"{on.monthly_fee:,} Ft",
        )
        print(
            "Contract:",
            f"{on.duration} months / {on.mileage:,} km/year",
        )

        print("\n--- SWITCH OFF ---")
        print("aria-checked:", off.switch_checked)
        print(
            "Down payment:",
            f"{off.down_payment_percent:.0f}%",
        )
        print(
            "Monthly fee:",
            f"{off.monthly_fee:,} Ft",
        )
        print(
            "Contract:",
            f"{off.duration} months / {off.mileage:,} km/year",
        )

        assert on.switch_checked is True
        assert on.down_payment_percent == 20.0

        assert off.switch_checked is False
        assert off.down_payment_percent == 0.0

        assert on.duration == off.duration
        assert on.mileage == off.mileage

        assert on.monthly_fee > 0
        assert off.monthly_fee > 0

        assert (
            off.monthly_fee
            != on.monthly_fee
        )

        # With no initial payment the observed monthly fee should be higher.
        assert (
            off.monthly_fee
            > on.monthly_fee
        )

        print(
            "\nTEST PASSED - AYVENS EXPOSES TWO DIRECTLY OBSERVED "
            "FINANCIAL STATES: 20% INITIAL PAYMENT AND 0% INITIAL PAYMENT."
        )

        browser.close()


if __name__ == "__main__":
    main()
