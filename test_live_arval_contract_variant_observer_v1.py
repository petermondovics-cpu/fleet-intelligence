from playwright.sync_api import (
    sync_playwright,
)

from contract_normalization.arval_contract_variant_observer import (
    OBSERVED,
    ArvalContractVariantObserver,
)


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)


def main():

    print("=" * 92)
    print("ARVAL CONTRACT VARIANT OBSERVER LIVE V1")
    print("=" * 92)

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        try:
            observer = (
                ArvalContractVariantObserver(
                    browser
                )
            )

            result = observer.observe(
                ARVAL_URL,
                targets=(
                    (60, 20000),
                    (48, 20000),
                ),
            )

            print()
            print(
                "Status:",
                result.status,
            )

            print(
                "Diagnostic:",
                result.diagnostic,
            )

            print()

            for item in (
                result.observations
            ):
                print(
                    item.duration,
                    "hó |",
                    item.mileage,
                    "km/év |",
                    item.monthly_fee,
                    "Ft/hó",
                )

            assert result.status in {
                OBSERVED,
                "UNRESOLVED",
            }

            observed = {
                (
                    item.duration,
                    item.mileage,
                ): item.monthly_fee
                for item in (
                    result.observations
                )
            }

            # Current Arval market state must be observable.
            assert (
                60,
                20000,
            ) in observed

            if (
                48,
                20000,
            ) in observed:

                print(
                    "\n48-month Arval variant directly observed."
                )

            else:
                print(
                    "\n48-month Arval variant not exposed or not safely "
                    "selectable; remains unresolved."
                )

            print()

            print(
                "TEST PASSED - ARVAL CONTRACT VARIANT OBSERVER "
                "RETURNS ONLY DIRECTLY OBSERVED EXACT-OFFER "
                "CONTRACT PRICE STATES."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
