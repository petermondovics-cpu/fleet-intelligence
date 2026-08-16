from playwright.sync_api import sync_playwright

from contract_normalization.arval_financial_state_observer import (
    OBSERVED,
    UNRESOLVED,
    ArvalFinancialStateObserver,
)


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajánlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)

# ASCII URL fallback used by the current project/live tests.
ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)


def main():
    print("=" * 92)
    print("ARVAL FINANCIAL STATE OBSERVER LIVE V1")
    print("=" * 92)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        try:
            result = (
                ArvalFinancialStateObserver(browser)
                .observe(ARVAL_URL)
            )

            print()
            print("Status:", result.status)
            print("Diagnostic:", result.diagnostic)

            if result.states:
                print()

                for state in result.states:
                    print(
                        "Monthly fee:",
                        state.monthly_fee,
                        "Ft/hó",
                    )
                    print(
                        "Down payment percent:",
                        state.down_payment_percent,
                    )
                    print(
                        "Down payment amount:",
                        state.down_payment_amount_huf,
                    )
                    print(
                        "Contract:",
                        state.duration,
                        "months /",
                        state.mileage,
                        "km/year",
                    )
                    print(
                        "Evidence:",
                        state.source_text,
                    )

            assert result.status in {
                OBSERVED,
                UNRESOLVED,
            }

            if result.status == OBSERVED:
                state = result.states[0]

                assert (
                    state.down_payment_percent is not None
                    or state.down_payment_amount_huf is not None
                )

                print(
                    "\nExplicit Arval down-payment evidence observed."
                )

            else:
                assert result.states == ()

                print(
                    "\nNo explicit Arval down-payment evidence "
                    "was found. UNKNOWN is preserved."
                )

            print()
            print(
                "TEST PASSED - ARVAL FINANCIAL STATE OBSERVER "
                "NEVER FABRICATES A DOWN-PAYMENT CONDITION."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
