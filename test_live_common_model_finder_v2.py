import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from urllib.parse import urlsplit, urlunsplit

from playwright.sync_api import sync_playwright


ARVAL_LIST_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "ajanlat-hosszu-tavu-igenyekre"
)

AYVENS_LIST_URL = "https://autotartosberlet.ayvens.com/"

MAX_CANDIDATES_TO_INSPECT = 30


@dataclass(frozen=True)
class Candidate:
    provider: str
    url: str
    brand_hint: str
    model_hint: str
    raw_slug: str


def clean_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, "", "")
    )


def normalize_token(text: str) -> str:
    text = text.casefold()

    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ö": "o",
        "ő": "o",
        "ú": "u",
        "ü": "u",
        "ű": "u",
    }

    for src, dst in replacements.items():
        text = text.replace(src, dst)

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    return " ".join(
        text.split()
    )


def dismiss_cookies(page):
    selectors = [
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
    ]

    for selector in selectors:
        locator = page.locator(selector)

        if locator.count() == 0:
            continue

        try:
            locator.first.click(timeout=2000)
            page.wait_for_timeout(300)
            return
        except Exception:
            continue


def parse_ayvens_url(url: str):
    path = [
        p
        for p in urlsplit(url).path.split("/")
        if p
    ]

    if len(path) != 2:
        return None

    brand = path[0]
    model = path[1]

    return (
        normalize_token(
            brand.replace("-", " ")
        ),
        normalize_token(
            model.replace("-", " ")
        ),
        model,
    )


def parse_arval_url(url: str):
    """
    Arval URLs are less regular.

    Examples:
      .../peugeot/peugeot-408-hybrid-145-e-dct6-allure-5d
      .../byd-atto-2-15-phev-boost-at/byd-atto-2-15-phev-boost-at
      .../renault-kangoo-15-blue-dci-95-extra-standard

    We use the last useful slug as raw identity evidence.
    Brand/model are only hints for candidate generation.
    """
    path = [
        p
        for p in urlsplit(url).path.split("/")
        if p
    ]

    if not path:
        return None

    last = path[-1]

    # If penultimate is an obvious brand directory, preserve it.
    known_brand_dir = None

    if len(path) >= 2:
        prev = path[-2]

        if (
            prev
            and prev != last
            and "-" not in prev
            and len(prev) < 25
        ):
            known_brand_dir = prev

    slug_tokens = [
        t
        for t in last.split("-")
        if t
    ]

    if not slug_tokens:
        return None

    brand = (
        known_brand_dir
        if known_brand_dir
        else slug_tokens[0]
    )

    # Build a broad model hint from the first few tokens after brand.
    after_brand = slug_tokens[:]

    if (
        after_brand
        and normalize_token(after_brand[0])
        == normalize_token(brand)
    ):
        after_brand = after_brand[1:]

    # Stop at obvious technical/version tokens.
    stop_pattern = re.compile(
        r"^(?:"
        r"\d+(?:\.\d+)?|"
        r"\d+kwh|"
        r"\d+kw|"
        r"\d+hp|"
        r"\d+le|"
        r"phev|hev|mhev|ev|"
        r"hybrid|dizel|diesel|benzin|petrol|"
        r"turbo|blue|dci|tdi|tsi|"
        r"at|awd|4x4|"
        r"edition|comfort|boost|design|"
        r"allure|gs|extra|standard"
        r")$",
        re.I,
    )

    model_tokens = []

    for token in after_brand:
        if stop_pattern.match(token):
            break

        model_tokens.append(token)

        if len(model_tokens) >= 4:
            break

    if not model_tokens:
        model_tokens = after_brand[:2]

    model = " ".join(model_tokens)

    return (
        normalize_token(
            brand.replace("-", " ")
        ),
        normalize_token(
            model.replace("-", " ")
        ),
        last,
    )


def discover_arval(page):
    page.goto(
        ARVAL_LIST_URL,
        wait_until="domcontentloaded",
        timeout=60000,
    )
    page.wait_for_timeout(2200)
    dismiss_cookies(page)

    hrefs = page.locator(
        "a[href*='/tartos-berleti-ajantlat/']"
    ).evaluate_all(
        "els => els.map(a => a.href)"
    )

    out = {}

    for href in hrefs:
        url = clean_url(href)

        parsed = parse_arval_url(url)

        if parsed is None:
            continue

        brand, model, raw_slug = parsed

        out[url] = Candidate(
            provider="Arval",
            url=url,
            brand_hint=brand,
            model_hint=model,
            raw_slug=raw_slug,
        )

    return list(out.values())


def discover_ayvens(page):
    page.goto(
        AYVENS_LIST_URL,
        wait_until="domcontentloaded",
        timeout=60000,
    )
    page.wait_for_timeout(2200)
    dismiss_cookies(page)

    hrefs = page.locator(
        "a[href]"
    ).evaluate_all(
        "els => els.map(a => a.href)"
    )

    out = {}

    for href in hrefs:
        url = clean_url(href)

        if "autotartosberlet.ayvens.com/" not in url:
            continue

        parsed = parse_ayvens_url(url)

        if parsed is None:
            continue

        brand, model, raw_slug = parsed

        if brand in {
            "",
            "rovidtavu autoberles",
            "szolgaltatasunk",
            "magazin",
            "ajanlatkeres",
        }:
            continue

        out[url] = Candidate(
            provider="Ayvens",
            url=url,
            brand_hint=brand,
            model_hint=model,
            raw_slug=raw_slug,
        )

    return list(out.values())


def candidate_score(
    arval: Candidate,
    ayvens: Candidate,
):
    if (
        arval.brand_hint
        != ayvens.brand_hint
    ):
        return 0.0

    a_model = arval.model_hint
    y_model = ayvens.model_hint

    if not a_model or not y_model:
        return 0.0

    # Strong token containment first.
    if (
        a_model in y_model
        or y_model in a_model
    ):
        return 1.0

    a_tokens = set(
        a_model.split()
    )
    y_tokens = set(
        y_model.split()
    )

    overlap = (
        len(a_tokens & y_tokens)
        / max(
            1,
            min(
                len(a_tokens),
                len(y_tokens),
            ),
        )
    )

    sequence = SequenceMatcher(
        None,
        a_model,
        y_model,
    ).ratio()

    return max(
        overlap,
        sequence,
    )


def make_pairs(
    arval,
    ayvens,
):
    rows = []

    for a in arval:
        for y in ayvens:
            score = candidate_score(
                a,
                y,
            )

            if score >= 0.55:
                rows.append(
                    (score, a, y)
                )

    rows.sort(
        key=lambda row: row[0],
        reverse=True,
    )

    return rows


def inspect_pair(
    browser,
    arval_candidate,
    ayvens_candidate,
):
    from scrapers.arval.evidence_aware_builder import (
        ArvalEvidenceAwareBuilder,
    )
    from scrapers.ayvens.evidence_aware_builder import (
        AyvensEvidenceAwareBuilder,
    )

    ap = browser.new_page()
    yp = browser.new_page()

    try:
        ap.goto(
            arval_candidate.url,
            wait_until="domcontentloaded",
            timeout=60000,
        )
        ap.wait_for_timeout(1500)
        dismiss_cookies(ap)

        arval = (
            ArvalEvidenceAwareBuilder()
            .build(ap)
        )

        yp.goto(
            ayvens_candidate.url,
            wait_until="domcontentloaded",
            timeout=60000,
        )
        yp.wait_for_timeout(1500)
        dismiss_cookies(yp)

        ayvens = (
            AyvensEvidenceAwareBuilder()
            .build(yp)
        )

        ac = arval.composite
        yc = ayvens.composite

        same_brand = (
            normalize_token(
                ac.offer.brand
            )
            == normalize_token(
                yc.offer.brand
            )
        )

        same_model = (
            normalize_token(
                ac.offer.model
            )
            == normalize_token(
                yc.offer.model
            )
        )

        same_fuel = (
            normalize_token(
                ac.offer.fuel_type
            )
            == normalize_token(
                yc.offer.fuel_type
            )
        )

        return (
            arval,
            ayvens,
            same_brand,
            same_model,
            same_fuel,
        )

    finally:
        ap.close()
        yp.close()


def main():

    print("=" * 80)
    print(
        "ARVAL ↔ AYVENS COMMON MODEL FINDER V2"
    )
    print("=" * 80)

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        arval = discover_arval(
            page
        )

        ayvens = discover_ayvens(
            page
        )

        print(
            f"\nArval URLs: {len(arval)}"
        )

        for item in arval:
            print(
                " A:",
                item.brand_hint,
                "/",
                item.model_hint,
                "->",
                item.raw_slug,
            )

        print(
            f"\nAyvens URLs: {len(ayvens)}"
        )

        pairs = make_pairs(
            arval,
            ayvens,
        )

        print(
            f"\nCandidate pairs: "
            f"{len(pairs)}"
        )

        for index, (
            score,
            a,
            y,
        ) in enumerate(
            pairs[:20],
            start=1,
        ):
            print(
                f"{index:02d}. "
                f"{score:.2f} | "
                f"{a.brand_hint} "
                f"{a.model_hint} "
                f"<-> "
                f"{y.brand_hint} "
                f"{y.model_hint}"
            )

        if not pairs:
            print(
                "\nNO URL-LEVEL COMMON MODEL "
                "CANDIDATES FOUND."
            )

            browser.close()
            return

        print(
            "\n--- LIVE IDENTITY VALIDATION ---"
        )

        for index, (
            score,
            a,
            y,
        ) in enumerate(
            pairs[
                :MAX_CANDIDATES_TO_INSPECT
            ],
            start=1,
        ):

            print(
                f"\n[{index}] "
                f"{a.url}"
            )
            print(
                "    vs "
                f"{y.url}"
            )

            try:
                (
                    arval_offer,
                    ayvens_offer,
                    same_brand,
                    same_model,
                    same_fuel,
                ) = inspect_pair(
                    browser,
                    a,
                    y,
                )

            except Exception as exc:
                print(
                    "    SKIP:",
                    type(exc).__name__,
                    exc,
                )
                continue

            ac = arval_offer.composite
            yc = ayvens_offer.composite

            print(
                "    Arval :",
                ac.offer.brand,
                ac.offer.model,
                "/",
                ac.offer.trim,
                "/",
                ac.offer.fuel_type,
            )

            print(
                "    Ayvens:",
                yc.offer.brand,
                yc.offer.model,
                "/",
                yc.offer.trim,
                "/",
                yc.offer.fuel_type,
            )

            print(
                "    Match:",
                "brand=",
                same_brand,
                "model=",
                same_model,
                "fuel=",
                same_fuel,
            )

            if (
                same_brand
                and same_model
                and same_fuel
            ):
                print(
                    "\n>>> EXACT CORE MATCH FOUND"
                )

                from comparison.evidence_aware_comparable import (
                    EvidenceAwareComparableOfferEngine,
                )

                result = (
                    EvidenceAwareComparableOfferEngine()
                    .compare(
                        arval_offer,
                        ayvens_offer,
                    )
                )

                print(
                    "\nComparison status:",
                    result.status,
                )

                for reason in (
                    result.reasons
                ):
                    print(
                        "-",
                        reason.code,
                        ":",
                        reason.message,
                    )

                print(
                    "\nEquipment evidence:"
                )
                print(
                    "Arval :",
                    arval_offer
                    .equipment_evidence
                    .standard_status,
                    "/",
                    arval_offer
                    .equipment_evidence
                    .optional_status,
                )
                print(
                    "Ayvens:",
                    ayvens_offer
                    .equipment_evidence
                    .standard_status,
                    "/",
                    ayvens_offer
                    .equipment_evidence
                    .optional_status,
                )

                print(
                    "\nTEST PASSED - "
                    "LIVE COMMON MODEL FOUND "
                    "AND COMPARED"
                )

                browser.close()
                return

        print(
            "\nNO EXACT PARSED BRAND + MODEL + "
            "FUEL MATCH FOUND."
        )

        print(
            "URL-level candidates exist, so the "
            "next layer should be explicit vehicle "
            "identity normalization rather than "
            "loosening the hard comparison barrier."
        )

        browser.close()


if __name__ == "__main__":
    main()
