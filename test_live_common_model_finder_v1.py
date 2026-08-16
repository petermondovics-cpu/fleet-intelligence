import re
import sys
from dataclasses import dataclass
from difflib import SequenceMatcher
from urllib.parse import urljoin, urlsplit, urlunsplit

from playwright.sync_api import sync_playwright


ARVAL_LIST_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "ajanlat-hosszu-tavu-igenyekre"
)

AYVENS_LIST_URL = "https://autotartosberlet.ayvens.com/"

MAX_DETAIL_PAGES_PER_PROVIDER = 40
MIN_NAME_SIMILARITY = 0.62


@dataclass(frozen=True)
class Candidate:
    provider: str
    url: str
    anchor_text: str


def clean_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, "", "")
    )


def norm(text: str) -> str:
    text = text.casefold()
    text = (
        text.replace("š", "s")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ö", "o")
        .replace("ő", "o")
        .replace("ú", "u")
        .replace("ü", "u")
        .replace("ű", "u")
    )
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


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


def discover(page, provider, list_url):
    print(f"\nDiscovering {provider}: {list_url}")
    page.goto(
        list_url,
        wait_until="domcontentloaded",
        timeout=60000,
    )
    page.wait_for_timeout(2500)
    dismiss_cookies(page)

    rows = page.locator("a[href]").evaluate_all(
        """
        els => els.map(a => ({
            href: a.href,
            text: (a.innerText || a.textContent || '').trim()
        }))
        """
    )

    out = {}
    for row in rows:
        href = clean_url(row["href"])
        text = " ".join(row["text"].split())

        if provider == "Arval":
            if "/tartos-berleti-ajantlat/" not in href:
                continue
        else:
            if "autotartosberlet.ayvens.com/" not in href:
                continue
            path = urlsplit(href).path.strip("/").split("/")
            if len(path) != 2:
                continue
            if path[0] in {
                "assets", "flex", "promocio", "szolgaltatasunk",
                "rovidtavu-autoberles"
            }:
                continue

        if href not in out:
            out[href] = Candidate(
                provider=provider,
                url=href,
                anchor_text=text,
            )

    values = list(out.values())
    print(f"Discovered detail URLs: {len(values)}")
    return values


def candidate_pairs(arval, ayvens):
    scored = []
    for a in arval:
        an = norm(a.anchor_text or a.url)
        for y in ayvens:
            yn = norm(y.anchor_text or y.url)
            score = SequenceMatcher(None, an, yn).ratio()
            if score >= MIN_NAME_SIMILARITY:
                scored.append((score, a, y))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def inspect_pair(browser, a, y):
    from scrapers.arval.evidence_aware_builder import (
        ArvalEvidenceAwareBuilder,
    )
    from scrapers.ayvens.evidence_aware_builder import (
        AyvensEvidenceAwareBuilder,
    )

    ap = browser.new_page()
    yp = browser.new_page()

    try:
        ap.goto(a.url, wait_until="domcontentloaded", timeout=60000)
        ap.wait_for_timeout(1800)
        dismiss_cookies(ap)
        ao = ArvalEvidenceAwareBuilder().build(ap)

        yp.goto(y.url, wait_until="domcontentloaded", timeout=60000)
        yp.wait_for_timeout(1800)
        dismiss_cookies(yp)
        yo = AyvensEvidenceAwareBuilder().build(yp)

        ac = ao.composite
        yc = yo.composite

        same_brand = norm(ac.offer.brand) == norm(yc.offer.brand)
        same_model = norm(ac.offer.model) == norm(yc.offer.model)
        same_fuel = norm(ac.offer.fuel_type) == norm(yc.offer.fuel_type)

        return {
            "arval": ao,
            "ayvens": yo,
            "same_brand": same_brand,
            "same_model": same_model,
            "same_fuel": same_fuel,
            "exact_core_match": (
                same_brand and same_model and same_fuel
            ),
        }
    finally:
        ap.close()
        yp.close()


def main():
    print("=" * 80)
    print("ARVAL ↔ AYVENS COMMON MODEL FINDER V1")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        arval = discover(
            page, "Arval", ARVAL_LIST_URL
        )[:MAX_DETAIL_PAGES_PER_PROVIDER]

        ayvens = discover(
            page, "Ayvens", AYVENS_LIST_URL
        )[:MAX_DETAIL_PAGES_PER_PROVIDER]

        pairs = candidate_pairs(arval, ayvens)

        print(f"\nName-level candidate pairs: {len(pairs)}")

        if not pairs:
            print(
                "\nNO CANDIDATES FOUND.\n"
                "This is not a comparison failure; discovery selectors "
                "or the current live inventories may need review."
            )
            browser.close()
            return

        exact = []

        for index, (score, a, y) in enumerate(pairs[:20], start=1):
            print(
                f"\n[{index}] inspecting candidate "
                f"(name similarity {score:.2f})"
            )
            print(" Arval :", a.anchor_text or a.url)
            print(" Ayvens:", y.anchor_text or y.url)

            try:
                result = inspect_pair(browser, a, y)
            except Exception as exc:
                print(" SKIP:", type(exc).__name__, exc)
                continue

            ac = result["arval"].composite
            yc = result["ayvens"].composite

            print(
                " Parsed Arval :",
                ac.offer.brand,
                ac.offer.model,
                "/",
                ac.offer.trim,
                "/",
                ac.offer.fuel_type,
            )
            print(
                " Parsed Ayvens:",
                yc.offer.brand,
                yc.offer.model,
                "/",
                yc.offer.trim,
                "/",
                yc.offer.fuel_type,
            )

            if result["exact_core_match"]:
                exact.append((a, y, result))
                print(" >>> EXACT CORE MATCH FOUND")
                break

        if not exact:
            print(
                "\nNO EXACT BRAND + MODEL + FUEL MATCH FOUND "
                "IN INSPECTED CANDIDATES."
            )
            print(
                "Do NOT loosen the comparison barrier automatically. "
                "A model-alias/derivative normalization layer should be "
                "introduced only with explicit evidence."
            )
            browser.close()
            return

        a, y, result = exact[0]
        ao = result["arval"]
        yo = result["ayvens"]

        print("\n" + "=" * 80)
        print("COMMON LIVE PAIR")
        print("=" * 80)
        print("ARVAL URL :", a.url)
        print("AYVENS URL:", y.url)

        from comparison.evidence_aware_comparable import (
            EvidenceAwareComparableOfferEngine,
        )

        comparison = EvidenceAwareComparableOfferEngine().compare(
            ao, yo
        )

        print("\nComparison status:", comparison.status)
        for reason in comparison.reasons:
            print("-", reason.code, ":", reason.message)

        print("\nEquipment evidence:")
        print(
            "Arval :",
            ao.equipment_evidence.standard_status,
            "/",
            ao.equipment_evidence.optional_status,
        )
        print(
            "Ayvens:",
            yo.equipment_evidence.standard_status,
            "/",
            yo.equipment_evidence.optional_status,
        )

        print("\nTEST PASSED - COMMON MODEL FINDER COMPLETED")
        browser.close()


if __name__ == "__main__":
    main()
