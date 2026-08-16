import re
from playwright.sync_api import sync_playwright


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)


MARKER = re.compile(
    r"6\s+szolgáltatás\s+az\s+Arvaltól\s+a\s+csomagban",
    re.IGNORECASE,
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


def meta(locator):
    return locator.evaluate(
        """
        el => ({
            tag: el.tagName,
            id: el.id || null,
            class: el.className || null,
            role: el.getAttribute('role'),
            dataTestId: el.getAttribute('data-testid'),
            ariaLabel: el.getAttribute('aria-label')
        })
        """
    )


def safe_text(locator):
    try:
        return " ".join(locator.inner_text().split())
    except Exception:
        return ""


def main():
    print("=" * 100)
    print("ARVAL EXACT-OFFER SERVICE PACKAGE DOM DIAGNOSTIC V2")
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

            # Find visible elements whose own text contains the package marker.
            candidates = page.locator("h1,h2,h3,h4,h5,p,span,div,section,article")

            matches = []

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

                if not MARKER.search(text):
                    continue

                # Avoid giant containers unless no smaller marker exists.
                matches.append((len(text), item, text))

            matches.sort(key=lambda x: x[0])

            print()
            print("MARKER MATCH COUNT:", len(matches))

            if not matches:
                print("No visible package marker element found.")
                return

            # Inspect up to the 5 smallest DOM nodes containing the marker.
            for match_index, (_, item, text) in enumerate(matches[:5], start=1):

                print()
                print("=" * 100)
                print("MARKER NODE", match_index)
                print("=" * 100)

                try:
                    print("attrs:", meta(item))
                except Exception:
                    print("attrs: {}")

                print("text:", text[:1500])

                # Parent chain.
                current = item

                for level in range(0, 8):

                    try:
                        current = current.locator("..")
                        if current.count() == 0:
                            break

                        parent_text = safe_text(current)

                        print()
                        print(f"PARENT LEVEL {level + 1}")

                        try:
                            print("attrs:", meta(current))
                        except Exception:
                            print("attrs: {}")

                        print("text:", parent_text[:2500])

                    except Exception:
                        break

                # Siblings around the marker node.
                print()
                print("--- DIRECT SIBLINGS ---")

                try:
                    sibling_info = item.evaluate(
                        """
                        el => {
                            const parent = el.parentElement;
                            if (!parent) return [];
                            return Array.from(parent.children).map((node, idx) => ({
                                idx,
                                tag: node.tagName,
                                id: node.id || null,
                                class: node.className || null,
                                text: (node.innerText || "").replace(/\\s+/g, " ").trim().slice(0, 2000)
                            }));
                        }
                        """
                    )
                except Exception:
                    sibling_info = []

                for sibling in sibling_info[:30]:
                    print()
                    print(
                        f"SIBLING {sibling.get('idx')} | "
                        f"{sibling.get('tag')} | "
                        f"id={sibling.get('id')} | "
                        f"class={sibling.get('class')}"
                    )
                    print("text:", sibling.get("text"))

            print()
            print("=" * 100)
            print(
                "DIAGNOSTIC COMPLETE - NO SERVICE INCLUSION WAS INFERRED."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
