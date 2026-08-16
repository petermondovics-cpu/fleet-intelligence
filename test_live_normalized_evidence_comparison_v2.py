from playwright.sync_api import sync_playwright

from scrapers.arval.evidence_aware_builder import (
    ArvalEvidenceAwareBuilder,
)
from scrapers.ayvens.evidence_aware_builder import (
    AyvensEvidenceAwareBuilder,
)
from comparison.normalized_evidence_aware import (
    NormalizedEvidenceAwareComparableEngine,
)


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)

AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)


def dismiss(page):
    for selector in [
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
    ]:
        loc = page.locator(selector)

        if loc.count() == 0:
            continue

        try:
            loc.first.click(timeout=2000)
            page.wait_for_timeout(300)
            return
        except Exception:
            pass


def load(browser, url, builder):
    page = browser.new_page()

    try:
        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_timeout(1800)
        dismiss(page)
        return builder.build(page)
    finally:
        page.close()


def main():

    print("=" * 80)
    print(
        "LIVE NORMALIZED EVIDENCE-AWARE "
        "COMPARISON V2"
    )
    print("=" * 80)

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        arval = load(
            browser,
            ARVAL_URL,
            ArvalEvidenceAwareBuilder(),
        )

        ayvens = load(
            browser,
            AYVENS_URL,
            AyvensEvidenceAwareBuilder(),
        )

        result = (
            NormalizedEvidenceAwareComparableEngine()
            .compare(
                arval,
                ayvens,
            )
        )

        print(
            "\nArval:",
            arval.composite.offer.model,
            "/",
            arval.composite.offer.trim,
            "/",
            arval.composite.duration,
            "hó",
        )

        print(
            "Ayvens:",
            ayvens.composite.offer.model,
            "/",
            ayvens.composite.offer.trim,
            "/",
            ayvens.composite.duration,
            "hó",
        )

        print(
            "\nEquipment evidence:"
        )

        print(
            "Arval :",
            arval.equipment_evidence.standard_status,
            "/",
            arval.equipment_evidence.optional_status,
        )

        print(
            "Ayvens:",
            ayvens.equipment_evidence.standard_status,
            "/",
            ayvens.equipment_evidence.optional_status,
        )

        print(
            "\nStatus:",
            result.status,
        )

        for reason in result.reasons:
            print(
                "-",
                reason.code,
                ":",
                reason.message,
            )

        assert (
            result.status
            == "INSUFFICIENT_EVIDENCE"
        )

        codes = {
            r.code
            for r in result.reasons
        }

        assert (
            "VEHICLE_VARIANT_DIFFERENCE"
            in codes
        )

        assert (
            "EQUIPMENT_EVIDENCE_INCOMPLETE"
            in codes
        )

        assert (
            "VEHICLE_TRIM_MISMATCH"
            not in codes
        )

        print(
            "\nTEST PASSED - "
            "LIVE TRIM DIFFERENCE NO LONGER "
            "CREATES FALSE HARD MISMATCH"
        )

        browser.close()


if __name__ == "__main__":
    main()
