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


PAIRS = [
    (
        "BYD ATTO 2",
        (
            "https://www.arval.hu/kis-es-kozepvallalkozasok/"
            "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
            "byd-atto-2-15-phev-boost-at"
        ),
        (
            "https://autotartosberlet.ayvens.com/"
            "byd/atto-2-dm-i"
        ),
    ),
    (
        "BYD SEAL U",
        (
            "https://www.arval.hu/kis-es-kozepvallalkozasok/"
            "tartos-berleti-ajantlat/"
            "byd-seal-u-phev-dm-i-comfort-at/"
            "byd-seal-u-phev-dm-i-comfort-at"
        ),
        (
            "https://autotartosberlet.ayvens.com/"
            "byd/seal-u-dm-i"
        ),
    ),
]


def dismiss_cookies(page):
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


def build(browser, url, builder):
    page = browser.new_page()

    try:
        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_timeout(1800)
        dismiss_cookies(page)
        return builder.build(page)
    finally:
        page.close()


def main():

    print("=" * 80)
    print(
        "LIVE NORMALIZED EVIDENCE-AWARE "
        "COMPARISON V1"
    )
    print("=" * 80)

    engine = (
        NormalizedEvidenceAwareComparableEngine()
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        for name, arval_url, ayvens_url in PAIRS:

            print(
                f"\n--- {name} ---"
            )

            arval = build(
                browser,
                arval_url,
                ArvalEvidenceAwareBuilder(),
            )

            ayvens = build(
                browser,
                ayvens_url,
                AyvensEvidenceAwareBuilder(),
            )

            ac = arval.composite
            yc = ayvens.composite

            print(
                "Arval :",
                ac.offer.brand,
                ac.offer.model,
                "/",
                ac.offer.trim,
                "/",
                ac.offer.fuel_type,
                "/",
                ac.duration,
                "hó /",
                f"{ac.mileage:,} km",
            )

            print(
                "Ayvens:",
                yc.offer.brand,
                yc.offer.model,
                "/",
                yc.offer.trim,
                "/",
                yc.offer.fuel_type,
                "/",
                yc.duration,
                "hó /",
                f"{yc.mileage:,} km",
            )

            result = engine.compare(
                arval,
                ayvens,
            )

            print(
                "Status:",
                result.status,
            )

            for reason in result.reasons:
                print(
                    "-",
                    reason.code,
                    ":",
                    reason.message,
                )

            assert not hasattr(
                result,
                "price_winner",
            )

        browser.close()

    print(
        "\nLIVE NORMALIZED EVIDENCE-AWARE "
        "COMPARISON V1 COMPLETED"
    )


if __name__ == "__main__":
    main()
