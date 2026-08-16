from playwright.sync_api import sync_playwright

from scrapers.arval.evidence_aware_builder import (
    ArvalEvidenceAwareBuilder,
)
from scrapers.ayvens.evidence_aware_builder import (
    AyvensEvidenceAwareBuilder,
)
from comparison.normalized_vehicle_identity import (
    NormalizedVehicleComparabilityEngine,
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
    (
        "BYD SEALION 7",
        (
            "https://www.arval.hu/kis-es-kozepvallalkozasok/"
            "tartos-berleti-ajantlat/"
            "byd-sealion-7-825kwh-design-awd/"
            "byd-sealion-7-825-kwh-design-awd"
        ),
        (
            "https://autotartosberlet.ayvens.com/"
            "byd/sealion-7"
        ),
    ),
]


def dismiss_cookies(page):
    selectors = [
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
    ]

    for selector in selectors:
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
        page.wait_for_timeout(2000)
        dismiss_cookies(page)
        return builder.build(page)
    finally:
        page.close()


def main():

    print("=" * 80)
    print(
        "LIVE VEHICLE IDENTITY NORMALIZATION V1"
    )
    print("=" * 80)

    engine = (
        NormalizedVehicleComparabilityEngine()
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        for name, arval_url, ayvens_url in PAIRS:

            print(
                f"\n--- {name} ---"
            )

            try:
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

            except Exception as exc:
                print(
                    "SKIP:",
                    type(exc).__name__,
                    exc,
                )
                continue

            pair = engine.normalize_pair(
                arval,
                ayvens,
            )

            print(
                "Arval raw:",
                arval.composite.offer.brand,
                arval.composite.offer.model,
                "/",
                arval.composite.offer.fuel_type,
            )

            print(
                "Ayvens raw:",
                ayvens.composite.offer.brand,
                ayvens.composite.offer.model,
                "/",
                ayvens.composite.offer.fuel_type,
            )

            print(
                "Canonical:",
                pair.left_brand,
                pair.left_model,
                pair.left_fuel,
                "<->",
                pair.right_brand,
                pair.right_model,
                pair.right_fuel,
            )

            result = (
                engine.compare_identity(
                    arval,
                    ayvens,
                )
            )

            print(
                "Identity status:",
                result.status,
            )

            for reason in result.reasons:
                print(
                    "-",
                    reason.code,
                    ":",
                    reason.message,
                )

        browser.close()

    print(
        "\nLIVE VEHICLE IDENTITY "
        "NORMALIZATION V1 COMPLETED"
    )


if __name__ == "__main__":
    main()
