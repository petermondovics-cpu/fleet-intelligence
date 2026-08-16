from playwright.sync_api import sync_playwright

from comparison.arval_exact_offer_service_evidence_resolver import (
    ArvalExactOfferServiceEvidenceResolver,
)


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)


def main():

    print("=" * 100)
    print("ARVAL EXACT-OFFER SERVICE EVIDENCE RESOLVER LIVE V1")
    print("=" * 100)

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        try:
            result = (
                ArvalExactOfferServiceEvidenceResolver(
                    browser
                )
                .resolve(
                    ARVAL_URL
                )
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
            print(
                "Promotable codes:",
                result.promotable_codes,
            )
            print(
                "Generic/background codes:",
                result.generic_codes,
            )

            for idx, item in enumerate(
                result.evidence,
                start=1,
            ):
                print()
                print(
                    "EVIDENCE",
                    idx,
                )
                print(
                    "Code:",
                    item.code,
                )
                print(
                    "Scope:",
                    item.applicability_scope,
                )
                print(
                    "Source type:",
                    item.source_type,
                )
                print(
                    "Text:",
                    item.source_text,
                )

            # Safety invariants.
            for item in result.evidence:
                if (
                    item.code
                    in result.promotable_codes
                ):
                    assert (
                        item.applicability_scope
                        == "EXACT_OFFER"
                    )

            assert not (
                set(result.promotable_codes)
                & set(result.generic_codes)
            )

            print()
            print(
                "TEST PASSED - ARVAL SERVICES ARE PROMOTED "
                "ONLY WHEN DIRECTLY OBSERVED INSIDE THE EXACT "
                "OFFER PACKAGE REGION; NON-PUBLICATION NEVER "
                "BECOMES EXCLUSION."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
