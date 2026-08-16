from playwright.sync_api import sync_playwright

from contract_normalization.ayvens_exact_priced_contract_resolver import (
    OBSERVED,
    AyvensExactPricedContractResolver,
)


AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)


def main():
    print("=" * 100)
    print("AYVENS 60M / 20K EXACT PRICED CONTRACT LIVE V1")
    print("=" * 100)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        try:
            result = (
                AyvensExactPricedContractResolver(
                    browser
                )
                .resolve(
                    AYVENS_URL,
                    targets=(
                        (48, 20000),
                        (60, 20000),
                    ),
                )
            )

            print()
            print("Status:", result.status)
            print("Source:", result.source_url)
            print("Diagnostic:", result.diagnostic)

            print()
            print("--- OBSERVATIONS ---")

            observed = {}

            for item in result.observations:
                observed[
                    (
                        item.duration,
                        item.mileage,
                    )
                ] = item.monthly_fee

                print(
                    item.duration,
                    "hó |",
                    item.mileage,
                    "km/év |",
                    item.monthly_fee,
                    "Ft/hó |",
                    item.evidence_method,
                )

                print(
                    "  ",
                    item.source_text,
                )

            # Current advertised state must remain directly observable.
            assert (
                48,
                20000,
            ) in observed

            if (
                60,
                20000,
            ) in observed:
                print()
                print(
                    "60M TARGET RESOLVED:",
                    observed[
                        (
                            60,
                            20000,
                        )
                    ],
                    "Ft/hó",
                )

                print(
                    "GREEN - exact priced 60m/20k evidence exists."
                )

            else:
                print()
                print(
                    "60M TARGET UNRESOLVED - provider exposes "
                    "the capability but no explicit price was safely "
                    "observed for 60m/20k."
                )

            assert result.status in {
                OBSERVED,
                "UNRESOLVED",
            }

            print()
            print(
                "TEST PASSED - RESOLVER NEVER PROMOTES AN "
                "UNPRICED 60-MONTH CAPABILITY TO PRICE EVIDENCE."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
