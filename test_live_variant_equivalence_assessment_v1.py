"""Live ATTO 2 variant-equivalence safety test.

Uses the established acquisition state explicitly. If your live builder import
names differ, adjust only those imports/build calls.
"""
from playwright.sync_api import sync_playwright
from comparison.variant_equivalence_assessor import (
    VARIANT_INSUFFICIENT_EVIDENCE, VariantEquivalenceAssessor)
from scrapers.arval.evidence_aware_builder import ArvalEvidenceAwareBuilder
from scrapers.ayvens.evidence_aware_builder import AyvensEvidenceAwareBuilder

ARVAL_URL = "https://www.arval.hu/kis-es-kozepvallalkozasok/tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/byd-atto-2-15-phev-boost-at"
AYVENS_URL = "https://autotartosberlet.ayvens.com/byd/atto-2-dm-i"

def main():
    print("=" * 80)
    print("LIVE VARIANT EQUIVALENCE ASSESSMENT V1")
    print("=" * 80)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ap, yp = browser.new_page(), browser.new_page()
        ap.goto(ARVAL_URL, wait_until="domcontentloaded", timeout=60000)
        yp.goto(AYVENS_URL, wait_until="domcontentloaded", timeout=60000)
        ap.wait_for_timeout(2000); yp.wait_for_timeout(2000)
        arval = ArvalEvidenceAwareBuilder().build(ap)
        ayvens = AyvensEvidenceAwareBuilder().build(yp)

        r = VariantEquivalenceAssessor().assess(
            arval, ayvens, "COMPARABLE",
            left_equipment_status="MANUFACTURER_VALIDATED",
            right_equipment_status="PARSING_UNRESOLVED")
        print("Status:", r.status)
        print("Identity:", r.identity_status)
        print("Trim differs:", r.trim_differs)
        print("Left equipment:", r.left_equipment_status)
        print("Right equipment:", r.right_equipment_status)
        for reason in r.reasons:
            print("-", reason)
        assert r.status == VARIANT_INSUFFICIENT_EVIDENCE
        assert r.price_comparison_safe is False
        browser.close()
    print("\nTEST PASSED - ATTO 2 VARIANT EQUIVALENCE REMAINS BLOCKED.")

if __name__ == "__main__":
    main()
