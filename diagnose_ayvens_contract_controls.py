from playwright.sync_api import sync_playwright

AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)


def main():

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        page.goto(
            AYVENS_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(2500)

        print("\n=== AYVENS CONTRACT DOM DIAGNOSTIC ===\n")

        # Print visible elements containing km/év.
        locators = page.locator(
            "p, span, div, button, label, "
            "[role='option'], [role='radio'], "
            "[role='button'], a"
        )

        found = 0

        for i in range(locators.count()):

            item = locators.nth(i)

            try:
                if not item.is_visible():
                    continue

                text = item.inner_text().strip()

            except Exception:
                continue

            if (
                "km/év" not in text.lower()
                and "km / év" not in text.lower()
            ):
                continue

            found += 1

            try:
                tag = item.evaluate(
                    "(el) => el.tagName"
                )

                classes = item.get_attribute(
                    "class"
                )

                role = item.get_attribute(
                    "role"
                )

                outer = item.evaluate(
                    "(el) => el.outerHTML"
                )

            except Exception:
                tag = "?"
                classes = ""
                role = ""
                outer = ""

            print(
                f"\n--- MATCH {found} ---"
            )

            print(
                f"TAG: {tag}"
            )

            print(
                f"ROLE: {role}"
            )

            print(
                f"CLASS: {classes}"
            )

            print(
                f"TEXT: {text[:500]}"
            )

            print(
                "OUTER HTML:"
            )

            print(
                outer[:2500]
            )

        print(
            f"\nTOTAL VISIBLE km/év MATCHES: "
            f"{found}"
        )

        # Also inspect clickable ancestors of the first
        # contract-summary paragraph.
        summaries = page.locator(
            "p.font-size-16px.font-source"
        )

        print(
            "\n=== AYVENS SUMMARY ANCESTORS ===\n"
        )

        for i in range(
            min(summaries.count(), 10)
        ):

            item = summaries.nth(i)

            try:
                if not item.is_visible():
                    continue

                text = item.inner_text().strip()

            except Exception:
                continue

            if (
                "hónap" not in text.lower()
                and "km/év" not in text.lower()
            ):
                continue

            print(
                f"\nSUMMARY {i}: {text}"
            )

            try:

                print(
                    item.evaluate(
                        """
                        (el) => {
                            let result = [];
                            let current = el;
                            for (let i = 0; i < 5 && current; i++) {
                                result.push({
                                    tag: current.tagName,
                                    class: current.className,
                                    role: current.getAttribute('role'),
                                    text: (current.innerText || '').slice(0, 1000)
                                });
                                current = current.parentElement;
                            }
                            return JSON.stringify(result, null, 2);
                        }
                        """
                    )
                )

            except Exception as exc:

                print(
                    f"Ancestor inspection failed: {exc}"
                )

        input(
            "\nPress ENTER to close browser..."
        )

        browser.close()


if __name__ == "__main__":
    main()
