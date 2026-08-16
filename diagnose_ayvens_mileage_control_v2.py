from playwright.sync_api import sync_playwright


AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)


def dump_element(label, locator):
    print("\n" + "=" * 80)
    print(label)
    print("=" * 80)

    try:
        print("COUNT:", locator.count())
    except Exception as exc:
        print("COUNT ERROR:", exc)
        return

    for i in range(locator.count()):
        item = locator.nth(i)

        try:
            if not item.is_visible():
                continue

            text = item.inner_text().strip()

        except Exception:
            continue

        print(f"\n--- ELEMENT {i} ---")
        print("TEXT:", repr(text[:1000]))

        try:
            print(
                "OUTER HTML:\n",
                item.evaluate(
                    "(el) => el.outerHTML"
                )[:5000],
            )
        except Exception as exc:
            print("HTML ERROR:", exc)


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

        page.wait_for_timeout(3000)

        print(
            "\n"
            + "=" * 80
        )
        print(
            "AYVENS MILEAGE CONTROL DIAGNOSTIC"
        )
        print(
            "=" * 80
        )

        # ------------------------------------------------
        # 1. Find every visible element containing 20.000
        # or 20000.
        # ------------------------------------------------

        for selector in [
            "text=20.000",
            "text=20000",
            "text=20 000",
            "text=km/év",
            "text=km / év",
        ]:

            dump_element(
                f"SELECTOR: {selector}",
                page.locator(selector),
            )

        # ------------------------------------------------
        # 2. Inspect elements containing the exact
        # mileage text and their parents.
        # ------------------------------------------------

        print(
            "\n"
            + "=" * 80
        )
        print(
            "ANCESTOR TREE FOR MILEAGE TEXT"
        )
        print(
            "=" * 80
        )

        candidates = page.locator(
            "p, span, div, label, button, "
            "input, select, option, "
            "[role='option'], [role='radio'], "
            "[role='button']"
        )

        found = 0

        for i in range(
            candidates.count()
        ):

            item = candidates.nth(i)

            try:
                if not item.is_visible():
                    continue

                text = item.inner_text().strip()

            except Exception:
                continue

            normalized = (
                text
                .lower()
                .replace(".", "")
                .replace(",", "")
                .replace(" ", "")
            )

            if (
                "20000" not in normalized
                and "20.000" not in text
            ):
                continue

            found += 1

            print(
                f"\n--- CANDIDATE {found} ---"
            )
            print(
                "TEXT:",
                repr(text[:1000])
            )

            try:

                tree = item.evaluate(
                    """
                    (el) => {
                        const result = [];
                        let current = el;

                        for (
                            let i = 0;
                            i < 7 && current;
                            i++
                        ) {
                            result.push({
                                level: i,
                                tag: current.tagName,
                                id: current.id,
                                className: current.className,
                                role: current.getAttribute('role'),
                                ariaLabel: current.getAttribute('aria-label'),
                                ariaValue: current.getAttribute('aria-valuetext'),
                                value: current.value ?? null,
                                type: current.getAttribute('type'),
                                text: (
                                    current.innerText || ''
                                ).slice(0, 500)
                            });

                            current = current.parentElement;
                        }

                        return result;
                    }
                    """
                )

                for node in tree:
                    print(node)

            except Exception as exc:
                print(
                    "TREE ERROR:",
                    exc
                )

        print(
            f"\nMileage candidates found: {found}"
        )

        # ------------------------------------------------
        # 3. Inspect all form controls.
        # ------------------------------------------------

        print(
            "\n"
            + "=" * 80
        )
        print(
            "ALL VISIBLE FORM CONTROLS"
        )
        print(
            "=" * 80
        )

        controls = page.locator(
            "input, select, textarea, button, "
            "[role='combobox'], "
            "[role='listbox'], "
            "[role='option'], "
            "[role='radio'], "
            "[role='button']"
        )

        control_count = 0

        for i in range(
            controls.count()
        ):

            item = controls.nth(i)

            try:
                if not item.is_visible():
                    continue

            except Exception:
                continue

            control_count += 1

            try:

                print(
                    f"\n--- CONTROL {control_count} ---"
                )

                print(
                    item.evaluate(
                        """
                        (el) => ({
                            tag: el.tagName,
                            id: el.id,
                            name: el.getAttribute('name'),
                            type: el.getAttribute('type'),
                            role: el.getAttribute('role'),
                            className: el.className,
                            value: el.value ?? null,
                            ariaLabel: el.getAttribute('aria-label'),
                            ariaValue: el.getAttribute('aria-valuetext'),
                            text: (el.innerText || '').slice(0, 500),
                            outerHTML: el.outerHTML.slice(0, 5000)
                        })
                        """
                    )
                )

            except Exception as exc:
                print(
                    "CONTROL ERROR:",
                    exc
                )

        print(
            f"\nVisible controls found: "
            f"{control_count}"
        )

        input(
            "\nPress ENTER to close browser..."
        )

        browser.close()


if __name__ == "__main__":
    main()
