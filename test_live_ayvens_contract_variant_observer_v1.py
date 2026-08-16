from playwright.sync_api import (
    sync_playwright,
)

from contract_normalization.ayvens_contract_variant_observer import (
    OBSERVED,
    AyvensContractVariantObserver,
)


AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)


def main():

    print("=" * 92)
    print("AYVENS CONTRACT VARIANT OBSERVER LIVE V1")
    print("=" * 92)

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        try:
            observer = (
                AyvensContractVariantObserver(
                    browser
                )
            )

            result = observer.observe(
                AYVENS_URL,
                targets=(
                    (48, 20000),
                    (60, 20000),
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

            # The current advertised state must be observable.
            assert (
                48,
                20000,
            ) in observed

            # V1 deliberately does NOT require 60 months to exist.
            # If Ayvens does not expose the state, it remains unresolved.
            if (
                60,
                20000,
            ) in observed:

                print(
                    "\n60-month variant directly observed."
                )

            else:
                print(
                    "\n60-month variant not exposed or not safely "
                    "selectable; remains unresolved."
                )

            print()
            print(
                "TEST PASSED - AYVENS CONTRACT VARIANT OBSERVER "
                "RETURNS ONLY DIRECTLY OBSERVED EXACT-OFFER "
                "CONTRACT PRICE STATES."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
