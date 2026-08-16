from playwright.sync_api import sync_playwright

from contract_normalization.arval_secondary_financial_evidence_resolver import (
    ArvalSecondaryFinancialEvidenceResolver,
)


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)


def main():
    print("=" * 100)
    print("ARVAL SECONDARY FINANCIAL EVIDENCE RESOLVER LIVE V1")
    print("=" * 100)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        try:
            result = (
                ArvalSecondaryFinancialEvidenceResolver(browser)
                .resolve(ARVAL_URL)
            )

            print()
            print("Status:", result.status)
            print("Diagnostic:", result.diagnostic)
            print("Evidence count:", len(result.evidence))
            print(
                "Promotable:",
                result.promotable_evidence is not None,
            )

            for idx, item in enumerate(result.evidence, start=1):
                print()
                print("EVIDENCE", idx)
                print("Scope:", item.applicability_scope)
                print("Source:", item.source_url)
                print("DP %:", item.down_payment_percent)
                print("DP amount:", item.down_payment_amount_huf)
                print("Text:", item.source_text)

            # Core safety invariant:
            # generic provider documentation must never become exact-offer
            # financial evidence.
            if result.promotable_evidence is not None:
                assert result.promotable_evidence.applicability_scope in {
                    "EXACT_OFFER",
                    "OFFER_LINKED_DOCUMENT",
                }

            for item in result.evidence:
                if (
                    item.applicability_scope
                    == "GENERIC_PROVIDER_DOCUMENTATION"
                ):
                    assert item is not result.promotable_evidence

            print()
            print(
                "TEST PASSED - ARVAL SECONDARY FINANCIAL RESOLVER "
                "NEVER PROMOTES GENERIC PROVIDER DOCUMENTATION TO "
                "EXACT-OFFER DOWN-PAYMENT EVIDENCE."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
