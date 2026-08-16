from playwright.sync_api import sync_playwright

from comparison.arval_exact_offer_service_evidence_resolver import (
    ArvalExactOfferServiceEvidenceResolver,
)


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)


EXPECTED = {
    "INSURANCE",
    "CLAIMS_MANAGEMENT",
    "FINANCING",
    "TYRES",
    "MAINTENANCE",
    "ROADSIDE_ASSISTANCE",
    "FLEET_PORTAL",
}


def main():
    print("=" * 100)
    print("ARVAL EXACT-OFFER SERVICE EVIDENCE RESOLVER LIVE V2")
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
                .resolve(ARVAL_URL)
            )

            print()
            print("Status:", result.status)
            print("Diagnostic:", result.diagnostic)
            print(
                "Promotable codes:",
                result.promotable_codes,
            )

            for idx, item in enumerate(
                result.evidence,
                start=1,
            ):
                print()
                print("EVIDENCE", idx)
                print("Code:", item.code)
                print("Label:", item.label)
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

                assert (
                    item.applicability_scope
                    == "EXACT_OFFER"
                )
                assert (
                    item.source_type
                    == "PROVIDER_OFFER_PAGE_DOM"
                )

            assert result.status == "VALIDATED"

            actual = set(
                result.promotable_codes
            )

            assert actual == EXPECTED, (
                f"Unexpected canonical service set: {actual}"
            )

            print()
            print(
                "TEST PASSED - ARVAL EXACT OFFER EXPOSES "
                "STRUCTURED SERVICE-WRAPPER EVIDENCE FOR ALL "
                "SIX DISPLAYED SERVICE BLOCKS, MAPPED "
                "CONSERVATIVELY TO CANONICAL SERVICE CODES."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
