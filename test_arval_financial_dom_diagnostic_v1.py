import re
from playwright.sync_api import sync_playwright

ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)

KEYWORDS = (
    "Ft", "Ft/hó", "hó", "hónap", "futamidő",
    "futásteljesítmény", "önerő", "kezdő befizetés",
    "induló befizetés", "kezdő bérleti díj",
    "első emelt bérleti díj", "nettó", "havidíj",
)

def dismiss(page):
    for selector in (
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
    ):
        loc = page.locator(selector)
        if loc.count() == 0:
            continue
        try:
            loc.first.click(timeout=1500)
            page.wait_for_timeout(200)
            return
        except Exception:
            pass

def attrs(locator):
    return locator.evaluate(
        """
        el => ({
            tag: el.tagName,
            id: el.id || null,
            class: el.className || null,
            role: el.getAttribute('role'),
            ariaLabel: el.getAttribute('aria-label'),
            dataTestId: el.getAttribute('data-testid'),
            itemprop: el.getAttribute('itemprop')
        })
        """
    )

def main():
    print("=" * 100)
    print("ARVAL FINANCIAL DOM DIAGNOSTIC V1")
    print("=" * 100)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        try:
            page = browser.new_page()
            page.goto(
                ARVAL_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(1800)
            dismiss(page)

            body = page.locator("body").inner_text()
            lowered = body.casefold()

            print("\n--- BODY KEYWORD HITS ---")
            for keyword in KEYWORDS:
                idx = lowered.find(keyword.casefold())
                if idx < 0:
                    continue
                start = max(0, idx - 180)
                end = min(len(body), idx + len(keyword) + 260)
                print("\nKEYWORD:", keyword)
                print(" ".join(body[start:end].split()))

            candidates = page.locator(
                "div, span, p, strong, b, h1, h2, h3, h4, button, label"
            )

            print("\n--- PRICE-LIKE VISIBLE TEXTS ---")
            seen = set()
            price_hits = []
            for i in range(candidates.count()):
                item = candidates.nth(i)
                try:
                    if not item.is_visible():
                        continue
                    text = " ".join(item.inner_text().split())
                except Exception:
                    continue
                if not text or len(text) > 500:
                    continue
                if not re.search(
                    r"(?i)\b\d{1,3}(?:[.\s]\d{3})+\s*Ft\b",
                    text,
                ):
                    continue
                if text in seen:
                    continue
                seen.add(text)
                try:
                    meta = attrs(item)
                except Exception:
                    meta = {}
                price_hits.append((text, meta))

            for idx, (text, meta) in enumerate(price_hits[:40], start=1):
                print(f"\nPRICE HIT {idx}")
                print("attrs:", meta)
                print("text:", text)

            print("\n--- FINANCIAL WORDING ELEMENTS ---")
            financial_terms = (
                "önerő", "kezdő befizetés", "induló befizetés",
                "kezdő bérleti díj", "első emelt bérleti díj",
                "nettó", "havidíj",
            )
            financial_hits = []
            financial_seen = set()

            for term in financial_terms:
                loc = page.get_by_text(
                    re.compile(re.escape(term), re.IGNORECASE)
                )
                for i in range(min(loc.count(), 20)):
                    item = loc.nth(i)
                    try:
                        if not item.is_visible():
                            continue
                        text = " ".join(item.inner_text().split())
                        meta = attrs(item)
                    except Exception:
                        continue

                    key = (
                        term.casefold(),
                        meta.get("tag"),
                        meta.get("id"),
                        str(meta.get("class")),
                        text,
                    )
                    if key in financial_seen:
                        continue
                    financial_seen.add(key)
                    financial_hits.append((term, text, meta))

            for idx, (term, text, meta) in enumerate(financial_hits[:50], start=1):
                print(f"\nFINANCIAL HIT {idx}")
                print("term:", term)
                print("attrs:", meta)
                print("text:", text)

            print("\n--- CONTRACT-LIKE ELEMENTS ---")
            contract_hits = []
            contract_seen = set()

            for i in range(candidates.count()):
                item = candidates.nth(i)
                try:
                    if not item.is_visible():
                        continue
                    text = " ".join(item.inner_text().split())
                except Exception:
                    continue

                if not text or len(text) > 500:
                    continue

                has_duration = bool(
                    re.search(r"(?i)\b\d{2}\s*(?:hónap|hó)\b", text)
                )
                has_mileage = bool(
                    re.search(
                        r"(?i)\b\d{1,3}(?:[.\s]\d{3})+\s*km\b",
                        text,
                    )
                )
                if not (has_duration or has_mileage):
                    continue

                try:
                    meta = attrs(item)
                except Exception:
                    meta = {}

                key = (text, str(meta))
                if key in contract_seen:
                    continue
                contract_seen.add(key)
                contract_hits.append((text, meta))

            for idx, (text, meta) in enumerate(contract_hits[:50], start=1):
                print(f"\nCONTRACT HIT {idx}")
                print("attrs:", meta)
                print("text:", text)

            print("\n--- RAW HTML SNIPPETS AROUND FT ---")
            html = page.content()
            matches = list(
                re.finditer(
                    r"(?i)\d{1,3}(?:[.\s]\d{3})+\s*Ft",
                    html,
                )
            )

            for idx, match in enumerate(matches[:20], start=1):
                start = max(0, match.start() - 350)
                end = min(len(html), match.end() + 500)
                snippet = re.sub(r"\s+", " ", html[start:end])
                print(f"\nHTML HIT {idx}")
                print(snippet)

            print("\n" + "=" * 100)
            print(
                "DIAGNOSTIC COMPLETE - NO FINANCIAL SEMANTICS WERE INFERRED."
            )
        finally:
            browser.close()

if __name__ == "__main__":
    main()
