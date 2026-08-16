from playwright.sync_api import sync_playwright


AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
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
            locator.first.click(
                timeout=2500
            )

            page.wait_for_timeout(
                500
            )

            print(
                "Cookie overlay handled"
            )

            return

        except Exception:
            continue

    print(
        "No active cookie overlay found"
    )


def print_locator_details(
    locator,
    label,
):

    print(
        "\n"
        + "=" * 88
    )

    print(label)

    print(
        "=" * 88
    )

    try:
        count = locator.count()
    except Exception as exc:
        print(
            "COUNT ERROR:",
            exc,
        )
        return

    print(
        "COUNT:",
        count,
    )

    for i in range(
        min(count, 30)
    ):

        item = locator.nth(i)

        try:

            if not item.is_visible():
                continue

            text = (
                item.inner_text()
                .strip()
            )

        except Exception:
            continue

        print(
            "\n"
            + "-" * 88
        )

        print(
            f"ITEM {i}"
        )

        print(
            "-" * 88
        )

        print(
            "TEXT:",
            repr(
                text[:4000]
            ),
        )

        try:

            data = item.evaluate(
                """
                (el) => {
                    const attrs = {};

                    for (const attr of el.attributes || []) {
                        attrs[attr.name] = attr.value;
                    }

                    return {
                        tag: el.tagName,
                        id: el.id || null,
                        className: el.className || null,
                        role: el.getAttribute('role'),
                        attrs,
                        outerHTML: el.outerHTML.slice(0, 12000)
                    };
                }
                """
            )

            print(
                "TAG:",
                data["tag"],
            )

            print(
                "ID:",
                data["id"],
            )

            print(
                "ROLE:",
                data["role"],
            )

            print(
                "CLASS:",
                data["className"],
            )

            print(
                "ATTRS:",
                data["attrs"],
            )

            print(
                "OUTER HTML:"
            )

            print(
                data["outerHTML"]
            )

        except Exception as exc:

            print(
                "DETAIL ERROR:",
                exc,
            )


def click_equipment_tab(
    page,
):

    print(
        "\n"
        + "=" * 88
    )

    print(
        "CLICKING ALAPFELSZERELTSÉG TAB"
    )

    print(
        "=" * 88
    )

    candidates = [
        page.get_by_text(
            "Alapfelszereltség",
            exact=True,
        ),
        page.locator(
            "button:has-text('Alapfelszereltség')"
        ),
        page.locator(
            "[role='tab']:has-text('Alapfelszereltség')"
        ),
        page.locator(
            "a:has-text('Alapfelszereltség')"
        ),
    ]

    for locator in candidates:

        if locator.count() == 0:
            continue

        for i in range(
            locator.count()
        ):

            item = locator.nth(i)

            try:

                if not item.is_visible():
                    continue

                print(
                    "Clicking:",
                    repr(
                        item.inner_text()
                        .strip()
                    ),
                )

                item.click(
                    timeout=5000
                )

                page.wait_for_timeout(
                    1200
                )

                return True

            except Exception as exc:

                print(
                    "Click candidate failed:",
                    exc,
                )

                continue

    return False


def inspect_after_click(
    page,
):

    print(
        "\n"
        + "=" * 88
    )

    print(
        "VISIBLE TEXT AFTER CLICK"
    )

    print(
        "=" * 88
    )

    body = (
        page.locator("body")
        .inner_text()
        .strip()
    )

    print(
        body[:20000]
    )

    print_locator_details(
        page.locator(
            "[role='tabpanel']"
        ),
        "ROLE=TABPANEL BLOCKS",
    )

    print_locator_details(
        page.locator(
            "[role='tab']"
        ),
        "ROLE=TAB ELEMENTS",
    )

    print_locator_details(
        page.locator(
            "ul li"
        ),
        "VISIBLE LI ELEMENTS",
    )

    print_locator_details(
        page.locator(
            "div[class*='equipment'], "
            "div[class*='Equipment'], "
            "div[class*='feature'], "
            "div[class*='Feature'], "
            "div[class*='spec'], "
            "div[class*='Spec']"
        ),
        "EQUIPMENT / FEATURE / SPEC CLASS BLOCKS",
    )

    # Capture likely leaf texts after the tab is active.
    print_locator_details(
        page.locator(
            "p, span, li, div"
        ).filter(
            has_text=""
        ),
        "GENERIC VISIBLE TEXT ELEMENTS",
    )


def main():

    print(
        "=" * 88
    )

    print(
        "AYVENS EQUIPMENT DOM DIAGNOSTIC V1"
    )

    print(
        "=" * 88
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        print(
            f"\nOpening Ayvens: {AYVENS_URL}"
        )

        page.goto(
            AYVENS_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(
            3000
        )

        dismiss_cookies(
            page
        )

        page.wait_for_timeout(
            800
        )

        clicked = click_equipment_tab(
            page
        )

        if not clicked:

            print(
                "\nERROR: "
                "Alapfelszereltség tab "
                "could not be clicked."
            )

            browser.close()

            raise SystemExit(1)

        print(
            "\nAlapfelszereltség tab clicked."
        )

        inspect_after_click(
            page
        )

        print(
            "\n"
            + "=" * 88
        )

        print(
            "DIAGNOSTIC COMPLETED"
        )

        print(
            "=" * 88
        )

        input(
            "\nPress ENTER to close browser..."
        )

        browser.close()


if __name__ == "__main__":
    main()
