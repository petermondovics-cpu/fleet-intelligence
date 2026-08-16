import sys
from playwright.sync_api import sync_playwright


DEFAULT_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)


KEYWORDS = [
    "felszereltség",
    "felszereltsége",
    "alapfelszereltség",
    "extra",
    "szolgáltatás",
    "szolgáltatások",
    "karbantartás",
    "gumi",
    "biztosítás",
    "assistance",
    "adó",
    "önerő",
    "induló",
    "kezdő",
    "befizetés",
    "havidíj",
    "futamidő",
    "futásteljesítmény",
]


def dismiss_cookies(page):

    selectors = [
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
        "button:has-text('Rendben')",
    ]

    for selector in selectors:
        locator = page.locator(selector)

        if locator.count() == 0:
            continue

        try:
            locator.first.click(timeout=2500)
            page.wait_for_timeout(500)
            print("Cookie overlay handled")
            return
        except Exception:
            continue

    print("No active cookie overlay found")


def print_keyword_matches(page):

    print("\n" + "=" * 88)
    print("KEYWORD DOM MATCHES")
    print("=" * 88)

    for keyword in KEYWORDS:

        locator = page.get_by_text(
            keyword,
            exact=False,
        )

        visible = []

        for i in range(
            min(locator.count(), 30)
        ):
            node = locator.nth(i)

            try:
                if not node.is_visible():
                    continue

                text = " ".join(
                    node.inner_text().split()
                )

                if not text:
                    continue

                visible.append(
                    (node, text)
                )
            except Exception:
                continue

        if not visible:
            continue

        print(
            f"\n### KEYWORD: {keyword!r} "
            f"({len(visible)} visible matches)"
        )

        for index, (
            node,
            text,
        ) in enumerate(
            visible[:8],
            start=1,
        ):

            print(
                f"\nMATCH {index}: "
                f"{text[:1000]!r}"
            )

            try:
                details = node.evaluate(
                    """
                    (el) => ({
                        tag: el.tagName,
                        id: el.id || null,
                        className:
                            typeof el.className === 'string'
                            ? el.className
                            : null,
                        role: el.getAttribute('role'),
                        ariaControls:
                            el.getAttribute('aria-controls'),
                        ariaSelected:
                            el.getAttribute('aria-selected'),
                        outerHTML:
                            el.outerHTML.slice(0, 5000)
                    })
                    """
                )

                print(
                    "TAG:",
                    details["tag"],
                )
                print(
                    "ID:",
                    details["id"],
                )
                print(
                    "ROLE:",
                    details["role"],
                )
                print(
                    "ARIA-CONTROLS:",
                    details["ariaControls"],
                )
                print(
                    "ARIA-SELECTED:",
                    details["ariaSelected"],
                )
                print(
                    "CLASS:",
                    details["className"],
                )
                print(
                    "HTML:",
                    details["outerHTML"],
                )

            except Exception as exc:
                print(
                    "DETAIL ERROR:",
                    exc,
                )


def print_semantic_blocks(page):

    selectors = {
        "HEADINGS": (
            "h1, h2, h3, h4, h5, h6"
        ),
        "TABS": (
            "[role='tab'], [role='tablist']"
        ),
        "TABPANELS": (
            "[role='tabpanel']"
        ),
        "LISTS": (
            "ul, ol"
        ),
        "DETAILS": (
            "details, summary"
        ),
        "ACCORDIONS / EXPANDERS": (
            "button[aria-expanded], "
            "[aria-expanded]"
        ),
    }

    for title, selector in (
        selectors.items()
    ):

        print("\n" + "=" * 88)
        print(title)
        print("=" * 88)

        locator = page.locator(selector)

        print(
            "COUNT:",
            locator.count(),
        )

        shown = 0

        for i in range(
            locator.count()
        ):

            node = locator.nth(i)

            try:
                if not node.is_visible():
                    continue

                text = " ".join(
                    node.inner_text().split()
                )
            except Exception:
                continue

            if not text:
                continue

            shown += 1

            print(
                f"\nITEM {shown}: "
                f"{text[:2500]!r}"
            )

            try:
                details = node.evaluate(
                    """
                    (el) => ({
                        tag: el.tagName,
                        id: el.id || null,
                        className:
                            typeof el.className === 'string'
                            ? el.className
                            : null,
                        role: el.getAttribute('role'),
                        ariaExpanded:
                            el.getAttribute('aria-expanded'),
                        outerHTML:
                            el.outerHTML.slice(0, 7000)
                    })
                    """
                )

                print(
                    "TAG:",
                    details["tag"],
                )
                print(
                    "ID:",
                    details["id"],
                )
                print(
                    "ROLE:",
                    details["role"],
                )
                print(
                    "ARIA-EXPANDED:",
                    details["ariaExpanded"],
                )
                print(
                    "CLASS:",
                    details["className"],
                )
                print(
                    "HTML:",
                    details["outerHTML"],
                )

            except Exception as exc:
                print(
                    "DETAIL ERROR:",
                    exc,
                )

            if shown >= 30:
                break


def click_likely_expanders(page):

    print("\n" + "=" * 88)
    print("TRYING RELEVANT EXPANDERS")
    print("=" * 88)

    locator = page.locator(
        "button, [role='button'], "
        "summary, a"
    )

    clicked = 0

    for i in range(
        locator.count()
    ):
        node = locator.nth(i)

        try:
            if not node.is_visible():
                continue

            text = " ".join(
                node.inner_text().split()
            )
        except Exception:
            continue

        lowered = text.lower()

        if not any(
            key in lowered
            for key in [
                "felszerelts",
                "részlete",
                "további",
                "szolgáltatás",
                "mit tartalmaz",
                "mutasd",
            ]
        ):
            continue

        print(
            "Candidate:",
            repr(text[:500]),
        )

        try:
            node.click(
                timeout=3000
            )
            page.wait_for_timeout(600)
            clicked += 1
            print("  CLICKED")
        except Exception as exc:
            print(
                "  CLICK FAILED:",
                exc,
            )

        if clicked >= 10:
            break

    print(
        "Expanders clicked:",
        clicked,
    )


def main():

    url = (
        sys.argv[1]
        if len(sys.argv) > 1
        else DEFAULT_URL
    )

    print("=" * 88)
    print("ARVAL OFFER DETAILS + EQUIPMENT DOM DIAGNOSTIC V1")
    print("=" * 88)
    print("\nURL:", url)

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page(
            viewport={
                "width": 1500,
                "height": 1100,
            }
        )

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(3000)

        dismiss_cookies(page)

        page.wait_for_timeout(800)

        print("\n" + "=" * 88)
        print("VISIBLE PAGE TEXT")
        print("=" * 88)

        body_text = (
            page.locator("body")
            .inner_text()
            .strip()
        )

        print(
            body_text[:30000]
        )

        print_keyword_matches(page)
        print_semantic_blocks(page)

        click_likely_expanders(page)

        if True:
            print("\n" + "=" * 88)
            print("AFTER EXPANDER CLICKS")
            print("=" * 88)

            print_keyword_matches(page)
            print_semantic_blocks(page)

        print("\n" + "=" * 88)
        print("DIAGNOSTIC COMPLETED")
        print("=" * 88)

        input(
            "\nPress ENTER to close browser..."
        )

        browser.close()


if __name__ == "__main__":
    main()
