import json
import re
from playwright.sync_api import sync_playwright


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
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
            ariaExpanded: el.getAttribute('aria-expanded'),
            ariaControls: el.getAttribute('aria-controls'),
            href: el.getAttribute('href'),
            hidden: el.hidden,
            style: el.getAttribute('style')
        })
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
    print("ARVAL SERVICE ACCORDION INTERACTION DIAGNOSTIC V3")
    print("=" * 100)

    requests = []
    responses = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

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
                ARVAL_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(1800)
            dismiss(page)

            offer_details = page.locator("#offer-details")
            assert offer_details.count() == 1, "#offer-details not found"

            accordion = offer_details.locator("ul.accordion")
            assert accordion.count() >= 1, "Accordion not found under #offer-details"

            item = accordion.locator("li.accordion-item").first
            title = item.locator("a.accordion-title").first

            print()
            print("--- BEFORE CLICK ---")
            print("TITLE ATTRS:", attrs(title))
            print("ITEM ATTRS:", attrs(item))
            print("ITEM TEXT:", safe_text(item))
            print("ITEM HTML:")
            print(safe_html(item)[:6000])

            before_req_count = len(requests)
            before_resp_count = len(responses)

            print()
            print("--- CLICK ---")

            title.click(timeout=3000)
            page.wait_for_timeout(1500)

            print()
            print("--- AFTER CLICK ---")
            print("TITLE ATTRS:", attrs(title))
            print("ITEM ATTRS:", attrs(item))
            print("ITEM TEXT:", safe_text(item))

            print()
            print("ITEM HTML:")
            print(safe_html(item)[:10000])

            print()
            print("--- CHILD ELEMENTS AFTER CLICK ---")

            children = item.locator(":scope > *")

            for i in range(children.count()):
                child = children.nth(i)

                try:
                    meta = attrs(child)
                except Exception:
                    meta = {}

                print()
                print(f"CHILD {i}")
                print("attrs:", meta)
                print("text:", safe_text(child)[:3000])

            print()
            print("--- DESCENDANTS WITH CONTENT-LIKE CLASSES ---")

            descendants = item.locator(
                "[class*='content'], "
                "[class*='accordion'], "
                "[id*='accordion'], "
                "[aria-labelledby], "
                "[role='region']"
            )

            seen = set()

            for i in range(descendants.count()):
                node = descendants.nth(i)

                html = safe_html(node)
                text = safe_text(node)

                key = (html[:500], text[:500])

                if key in seen:
                    continue

                seen.add(key)

                try:
                    meta = attrs(node)
                except Exception:
                    meta = {}

                print()
                print(f"DESCENDANT {i}")
                print("attrs:", meta)
                print("text:", text[:4000])

            print()
            print("--- SERVICE-LIKE TEXTS INSIDE ITEM ---")

            service_terms = (
                "biztosítás",
                "káresemény",
                "finanszírozás",
                "karbantartás",
                "szerviz",
                "gumi",
                "assistance",
                "segítségnyújtás",
                "adó",
                "portál",
            )

            item_text = safe_text(item)

            for term in service_terms:
                if term.casefold() in item_text.casefold():
                    print("FOUND:", term)

            print()
            print("--- NETWORK DELTA AFTER CLICK ---")

            new_requests = requests[before_req_count:]
            new_responses = responses[before_resp_count:]

            interesting_requests = [
                r for r in new_requests
                if r["resource_type"] in {
                    "xhr",
                    "fetch",
                    "document",
                    "script",
                }
            ]

            interesting_responses = [
                r for r in new_responses
                if any(
                    token in r["url"].casefold()
                    for token in (
                        "ajax",
                        "accordion",
                        "offer",
                        "service",
                        "api",
                        "json",
                    )
                )
            ]

            print("REQUESTS:")
            for req in interesting_requests[:50]:
                print(json.dumps(req, ensure_ascii=False))

            print()
            print("RESPONSES:")
            for resp in interesting_responses[:50]:
                print(json.dumps(resp, ensure_ascii=False))

            print()
            print("--- OFFER DETAILS FINAL TEXT ---")
            print(safe_text(offer_details)[:8000])

            print()
            print("=" * 100)
            print(
                "DIAGNOSTIC COMPLETE - NO SERVICE INCLUSION WAS INFERRED."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
