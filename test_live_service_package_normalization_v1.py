from playwright.sync_api import sync_playwright

from scrapers.arval.evidence_aware_builder import (
    ArvalEvidenceAwareBuilder,
)
from scrapers.ayvens.evidence_aware_builder import (
    AyvensEvidenceAwareBuilder,
)
from comparison.service_package_comparison import (
    ServicePackageComparisonEngine,
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
        "LIVE SERVICE PACKAGE NORMALIZATION V1"
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

        engine = (
            ServicePackageComparisonEngine()
        )

        result = engine.compare(
            arval.composite.services,
            ayvens.composite.services,
        )

        print(
            "\nStatus:",
            result.status,
        )

        print(
            "Arval-only canonical services:",
            result.left_only_codes,
        )

        print(
            "Ayvens-only canonical services:",
            result.right_only_codes,
        )

        print(
            "Arval unknown wording:",
            result.left_unknown,
        )

        print(
            "Ayvens unknown wording:",
            result.right_unknown,
        )

        for diff in result.differences:
            print(
                "DIFFERENCE:",
                diff.code,
                diff.left_included,
                diff.right_included,
            )

        browser.close()

    print(
        "\nLIVE SERVICE PACKAGE "
        "NORMALIZATION V1 COMPLETED"
    )


if __name__ == "__main__":
    main()
