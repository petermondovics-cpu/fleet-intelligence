from playwright.sync_api import sync_playwright

from scrapers.ayvens.parser import AyvensParser
from scrapers.ayvens.offer_details_parser import (
    AyvensOfferDetailsParser,
)


AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)


def dismiss_cookies(page):

    selectors = [
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
    ]

    for selector in selectors:

        locator = page.locator(selector)

        if locator.count() == 0:
            continue

        try:
            locator.first.click(
                timeout=2500
            )
            page.wait_for_timeout(500)

            print(
                "Cookie overlay handled"
            )

            return

        except Exception:
            continue

    print(
        "No active cookie overlay found"
    )


def main():

    print(
        "=" * 72
    )
    print(
        "AYVENS OFFER DETAILS LIVE TEST V1"
    )
    print(
        "=" * 72
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        print(
            f"\nOpening Ayvens: {AYVENS_URL}"
        )

        page.goto(
            AYVENS_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(
            3000
        )

        dismiss_cookies(
            page
        )

        page.wait_for_timeout(
            1000
        )

        base_parser = AyvensParser()
        details_parser = (
            AyvensOfferDetailsParser()
        )

        # ====================================================
        # ADVERTISED CONTRACT
        # ====================================================

        print(
            "\n--- ADVERTISED CONTRACT ---"
        )

        monthly_fee = (
            base_parser.parse_monthly_fee(
                page
            )
        )

        duration = (
            base_parser.parse_duration(
                page
            )
        )

        mileage = (
            base_parser.parse_mileage(
                page
            )
        )

        print(
            f"Monthly fee: "
            f"{monthly_fee:,} Ft"
        )

        print(
            f"Duration: "
            f"{duration} months"
        )

        print(
            f"Mileage: "
            f"{mileage:,} km/year"
        )

        assert monthly_fee > 0
        assert duration > 0
        assert mileage > 0

        print(
            "TEST 1 PASSED - "
            "ADVERTISED CONTRACT PARSED"
        )

        # ====================================================
        # SERVICES
        # ====================================================

        print(
            "\n--- SERVICES ---"
        )

        services = (
            details_parser.parse_services(
                page
            )
        )

        included = (
            services.included()
        )

        for item in included:
            print(
                f"INCLUDED: "
                f"{item.category} / "
                f"{item.name}"
            )

        assert len(included) >= 1

        expected_services = [
            (
                "MAINTENANCE",
                "Teljes körű karbantartás",
            ),
            (
                "TYRES",
                "Téli-, nyári gumiabroncs",
            ),
            (
                "MOBILITY",
                "Assistance szolgáltatás",
            ),
            (
                "ADMINISTRATION",
                "MyAyvens online ügyintézési rendszer",
            ),
            (
                "TAX",
                "Vonatkozó adók",
            ),
            (
                "INSURANCE",
                "Biztosítási csomag",
            ),
        ]

        missing = []

        for category, name in (
            expected_services
        ):

            if (
                services.has_service(
                    category,
                    name,
                )
                is not True
            ):
                missing.append(
                    f"{category} / {name}"
                )

        if missing:
            raise AssertionError(
                "Expected Ayvens services "
                "not found: "
                + "; ".join(missing)
            )

        print(
            "TEST 2 PASSED - "
            "ALL EXPECTED SERVICES PARSED"
        )

        # ====================================================
        # DOWN PAYMENT
        # ====================================================

        print(
            "\n--- DOWN PAYMENT ---"
        )

        down_payment = (
            details_parser
            .parse_down_payment(
                page
            )
        )

        print(
            "Percent:",
            down_payment.percent,
        )

        print(
            "Amount:",
            down_payment.amount,
        )

        print(
            "Status:",
            down_payment.status,
        )

        assert (
            down_payment.percent
            is None
        )

        assert (
            down_payment.amount
            is None
        )

        print(
            "TEST 3 PASSED - "
            "NO FALSE DOWN PAYMENT VALUE"
        )

        # ====================================================
        # QUOTE CAPABILITIES
        # ====================================================

        print(
            "\n--- QUOTE CAPABILITIES ---"
        )

        capabilities = (
            details_parser
            .parse_quote_capabilities(
                page
            )
        )

        print(
            "Duration:",
            capabilities.duration_min,
            "->",
            capabilities.duration_max,
            "step",
            capabilities.duration_step,
        )

        print(
            "Mileage:",
            capabilities.mileage_min,
            "->",
            capabilities.mileage_max,
            "step",
            capabilities.mileage_step,
        )

        assert (
            capabilities.duration_min
            is not None
        )

        assert (
            capabilities.duration_max
            is not None
        )

        assert (
            capabilities.mileage_min
            is not None
        )

        assert (
            capabilities.mileage_max
            is not None
        )

        assert not hasattr(
            capabilities,
            "monthly_fee",
        )

        print(
            "TEST 4 PASSED - "
            "QUOTE CAPABILITIES ARE "
            "NON-PRICING METADATA"
        )

        # ====================================================
        # FINANCIAL CONDITIONS
        # ====================================================

        print(
            "\n--- FINANCIAL CONDITIONS ---"
        )

        financial = (
            details_parser
            .build_financial_conditions(
                page,
                monthly_fee,
            )
        )

        assert (
            financial.monthly_fee
            == monthly_fee
        )

        assert (
            financial.down_payment.percent
            is None
        )

        assert (
            financial.down_payment.amount
            is None
        )

        print(
            f"Observed monthly fee: "
            f"{financial.monthly_fee:,} Ft"
        )

        print(
            "TEST 5 PASSED - "
            "FINANCIAL CONDITIONS BUILT"
        )

        # ====================================================
        # SAFETY BARRIER
        # ====================================================

        print(
            "\n--- SAFETY BARRIER ---"
        )

        print(
            "Advertised contract:"
        )
        print(
            f"  {duration} months / "
            f"{mileage:,} km/year / "
            f"{monthly_fee:,} Ft"
        )

        print(
            "Quote controls:"
        )
        print(
            f"  duration "
            f"{capabilities.duration_min}"
            f"-{capabilities.duration_max}"
        )
        print(
            f"  mileage "
            f"{capabilities.mileage_min:,}"
            f"-{capabilities.mileage_max:,}"
        )

        assert (
            duration
            >= capabilities.duration_min
        )
        assert (
            duration
            <= capabilities.duration_max
        )
        assert (
            mileage
            >= capabilities.mileage_min
        )
        assert (
            mileage
            <= capabilities.mileage_max
        )

        print(
            "TEST 6 PASSED - "
            "ADVERTISED CONTRACT KEPT "
            "SEPARATE FROM QUOTE CONTROLS"
        )

        print(
            "\n"
            + "=" * 72
        )

        print(
            "ALL AYVENS OFFER DETAILS "
            "LIVE V1 TESTS PASSED"
        )

        print(
            "=" * 72
        )

        browser.close()


if __name__ == "__main__":
    main()
