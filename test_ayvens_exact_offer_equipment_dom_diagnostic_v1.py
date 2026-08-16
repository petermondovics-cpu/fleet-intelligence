import json
import re
from playwright.sync_api import sync_playwright


AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)


KEYWORDS = (
    "felszereltség",
    "alapfelszereltség",
    "standard",
    "opció",
    "extra",
    "active",
    "166 hp",
    "kamera",
    "ülés",
    "kijelző",
    "led",
    "carplay",
    "android auto",
    "parkol",
    "fűthető",
    "panoráma",
    "wireless",
    "vezetéstámogató",
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
        el => {
            const out = {
                tag: el.tagName,
                id: el.id || null,
                class: el.className || null,
                role: el.getAttribute('role'),
                ariaLabel: el.getAttribute('aria-label'),
                ariaExpanded: el.getAttribute('aria-expanded'),
                ariaControls: el.getAttribute('aria-controls'),
                dataTestId: el.getAttribute('data-testid'),
                hidden: el.hidden,
                style: el.getAttribute('style')
            };

            for (const attr of Array.from(el.attributes || [])) {
                if (attr.name.startsWith('data-')) {
                    out[attr.name] = attr.value;
                }
            }

            return out;
        }
        """
    )


def safe_text(locator):
    try:
        return " ".join(locator.inner_text().split())
    except Exception:
        return ""


def safe_html(locator):
    try:
        return locator.evaluate("el => el.outerHTML")
    except Exception:
        return ""


def main():
    print("=" * 100)
    print("AYVENS EXACT-OFFER EQUIPMENT DOM DIAGNOSTIC V1")
    print("=" * 100)

    requests = []
    responses = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        try:
            page = browser.new_page()

            page.on(
                "request",
                lambda req: requests.append(
                    {
                        "method": req.method,
                        "resource_type": req.resource_type,
                        "url": req.url,
                    }
                ),
            )

            page.on(
                "response",
                lambda resp: responses.append(
                    {
                        "status": resp.status,
                        "url": resp.url,
                    }
                ),
            )

            page.goto(
                AYVENS_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            page.wait_for_timeout(1800)
            dismiss(page)

            body = page.locator("body").inner_text()

            print()
            print("--- OFFER IDENTITY ---")

            for pattern in (
                r"(?i)ATTO\s*2[^\\n]{0,100}",
                r"(?i)Active[^\\n]{0,100}",
                r"(?i)166\s*HP[^\\n]{0,100}",
            ):
                match = re.search(pattern, body)
                if match:
                    print("MATCH:", " ".join(match.group(0).split()))

            print()
            print("--- KEYWORD CONTEXTS ---")

            lower = body.casefold()

            for keyword in KEYWORDS:
                start = 0
                hit_no = 0

                while True:
                    idx = lower.find(
                        keyword.casefold(),
                        start,
                    )

                    if idx < 0:
                        break

                    hit_no += 1

                    lo = max(
                        0,
                        idx - 220,
                    )

                    hi = min(
                        len(body),
                        idx + len(keyword) + 420,
                    )

                    print()
                    print(
                        f"KEYWORD: {keyword} | HIT {hit_no}"
                    )
                    print(
                        " ".join(
                            body[lo:hi].split()
                        )
                    )

                    start = idx + len(keyword)

                    if hit_no >= 5:
                        break

            print()
            print("--- EQUIPMENT-LIKE VISIBLE ELEMENTS ---")

            candidates = page.locator(
                "li, div, span, p, strong, b, h2, h3, h4, "
                "button, label, section, article"
            )

            hits = []
            seen = set()

            equipment_pattern = re.compile(
                r"(?i)"
                r"(felszereltség|alapfelszereltség|standard|opció|extra|"
                r"kamera|ülés|kijelző|LED|CarPlay|Android Auto|"
                r"parkol|fűthető|panoráma|wireless|vezetéstámogató)"
            )

            for i in range(candidates.count()):
                item = candidates.nth(i)

                try:
                    if not item.is_visible():
                        continue
                except Exception:
                    continue

                text = safe_text(item)

                if not text:
                    continue

                if len(text) > 1000:
                    continue

                if not equipment_pattern.search(text):
                    continue

                try:
                    meta = attrs(item)
                except Exception:
                    meta = {}

                key = (
                    text,
                    str(meta),
                )

                if key in seen:
                    continue

                seen.add(key)
                hits.append(
                    (
                        len(text),
                        item,
                        text,
                        meta,
                    )
                )

            hits.sort(
                key=lambda x: x[0]
            )

            for idx, (
                _,
                item,
                text,
                meta,
            ) in enumerate(
                hits[:80],
                start=1,
            ):
                print()
                print(
                    f"EQUIPMENT HIT {idx}"
                )
                print(
                    "attrs:",
                    meta,
                )
                print(
                    "text:",
                    text,
                )

                try:
                    parent = item.locator("..")
                    print(
                        "parent attrs:",
                        attrs(parent),
                    )
                    print(
                        "parent text:",
                        safe_text(parent)[:1600],
                    )
                except Exception:
                    pass

            print()
            print("--- COLLAPSIBLE / TAB / ACCORDION CANDIDATES ---")

            interactive = page.locator(
                "[aria-expanded], "
                "[role='tab'], "
                "[role='tabpanel'], "
                "[role='button'], "
                "details, summary, "
                "[class*='accordion'], "
                "[class*='collapse'], "
                "[class*='tab']"
            )

            interactive_seen = set()

            for i in range(interactive.count()):
                item = interactive.nth(i)
                text = safe_text(item)

                try:
                    meta = attrs(item)
                except Exception:
                    meta = {}

                key = (
                    str(meta),
                    text[:400],
                )

                if key in interactive_seen:
                    continue

                interactive_seen.add(key)

                if (
                    text
                    and len(text) <= 1500
                ):
                    print()
                    print(
                        f"INTERACTIVE {i}"
                    )
                    print(
                        "attrs:",
                        meta,
                    )
                    print(
                        "text:",
                        text,
                    )

            print()
            print("--- HIDDEN EQUIPMENT-LIKE DOM ---")

            hidden_nodes = page.locator(
                "[hidden], "
                "[aria-hidden='true'], "
                "[style*='display: none'], "
                "[style*='display:none']"
            )

            hidden_count = 0

            for i in range(hidden_nodes.count()):
                item = hidden_nodes.nth(i)
                text = safe_text(item)

                if not text:
                    continue

                if not equipment_pattern.search(text):
                    continue

                hidden_count += 1

                try:
                    meta = attrs(item)
                except Exception:
                    meta = {}

                print()
                print(
                    f"HIDDEN HIT {hidden_count}"
                )
                print(
                    "attrs:",
                    meta,
                )
                print(
                    "text:",
                    text[:2500],
                )

                if hidden_count >= 40:
                    break

            print()
            print("--- JSON-LD / EMBEDDED SCRIPT HITS ---")

            scripts = page.locator(
                "script"
            )

            script_hits = 0

            for i in range(scripts.count()):
                script = scripts.nth(i)

                try:
                    text = (
                        script.text_content()
                        or ""
                    )
                except Exception:
                    continue

                if not text:
                    continue

                if not equipment_pattern.search(text):
                    continue

                script_hits += 1

                print()
                print(
                    f"SCRIPT HIT {script_hits}"
                )

                snippet = re.sub(
                    r"\s+",
                    " ",
                    text,
                )

                print(
                    snippet[:5000]
                )

                if script_hits >= 20:
                    break

            print()
            print("--- NETWORK CANDIDATES ---")

            for req in requests:
                if req["resource_type"] not in {
                    "xhr",
                    "fetch",
                    "document",
                }:
                    continue

                low = req["url"].casefold()

                if any(
                    token in low
                    for token in (
                        "vehicle",
                        "offer",
                        "product",
                        "config",
                        "equipment",
                        "spec",
                        "feature",
                        "api",
                        "json",
                    )
                ):
                    print(
                        json.dumps(
                            req,
                            ensure_ascii=False,
                        )
                    )

            print()
            print("--- RAW PAGE HTML KEYWORD SNIPPETS ---")

            html = page.content()
            html_lower = html.casefold()

            emitted = 0

            for keyword in KEYWORDS:
                idx = html_lower.find(
                    keyword.casefold()
                )

                if idx < 0:
                    continue

                lo = max(
                    0,
                    idx - 600,
                )

                hi = min(
                    len(html),
                    idx + len(keyword) + 1000,
                )

                snippet = re.sub(
                    r"\s+",
                    " ",
                    html[lo:hi],
                )

                emitted += 1

                print()
                print(
                    f"HTML HIT {emitted} | {keyword}"
                )
                print(
                    snippet[:3500]
                )

                if emitted >= 30:
                    break

            print()
            print("=" * 100)
            print(
                "DIAGNOSTIC COMPLETE - NO EQUIPMENT "
                "INCLUSION OR STANDARD/OPTIONAL STATUS "
                "WAS INFERRED."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
