from playwright.sync_api import sync_playwright


URL = "https://autotartosberlet.ayvens.com/byd/atto-2-dm-i"
LABEL = "Induló befizetés"


def clean(text):
    return " ".join((text or "").split())


def dismiss(page):
    for selector in (
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
    ):
        loc = page.locator(selector)
        if not loc.count():
            continue
        try:
            loc.first.click(timeout=1800)
            page.wait_for_timeout(300)
            return
        except Exception:
            pass


def describe(node, name):
    try:
        tag = node.evaluate("(el) => el.tagName")
    except Exception:
        tag = "?"

    attrs = {}
    for attr in (
        "role",
        "type",
        "id",
        "class",
        "aria-checked",
        "aria-selected",
        "aria-pressed",
        "aria-label",
        "data-p-checked",
        "data-state",
    ):
        try:
            attrs[attr] = node.get_attribute(attr)
        except Exception:
            attrs[attr] = None

    try:
        visible = node.is_visible()
    except Exception:
        visible = False

    try:
        text = clean(node.inner_text())
    except Exception:
        text = ""

    print(f"\n{name}")
    print("tag:", tag)
    print("visible:", visible)
    print("attrs:", attrs)
    print("text:", text[:1000])


def visible_fee_texts(page):
    selectors = (
        "text=/\\d[\\d .]*\\s*Ft\\s*\\/\\s*hó/i",
        "text=/\\d[\\d .]*\\s*Ft\\/hó/i",
        "[class*='price']",
        "[class*='Price']",
        "[class*='monthly']",
        "[class*='Monthly']",
    )

    out = []
    seen = set()

    for selector in selectors:
        loc = page.locator(selector)

        for i in range(loc.count()):
            node = loc.nth(i)

            try:
                if not node.is_visible():
                    continue
                text = clean(node.inner_text())
            except Exception:
                continue

            if not text:
                continue

            key = text.casefold()
            if key in seen:
                continue

            seen.add(key)
            out.append(text)

    return out


def state_snapshot(page, title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    fees = visible_fee_texts(page)

    print("\nVISIBLE PRICE-LIKE TEXTS:")
    for value in fees[:30]:
        print("-", value)

    body = clean(page.locator("body").inner_text())

    idx = body.casefold().find(LABEL.casefold())

    if idx >= 0:
        start = max(0, idx - 500)
        end = min(len(body), idx + 1500)
        print("\nBODY CONTEXT:")
        print(body[start:end])


def main():
    print("=" * 88)
    print("AYVENS FINANCIAL SWITCH DOM DIAGNOSTIC V1")
    print("=" * 88)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(
            URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_timeout(2500)
        dismiss(page)

        print("\nURL:", page.url)

        # ----------------------------------------------------
        # Find label/control neighborhood
        # ----------------------------------------------------
        print("\n--- LABEL MATCHES ---")

        labels = page.get_by_text(
            LABEL,
            exact=True,
        )

        print("Exact label count:", labels.count())

        for i in range(labels.count()):
            describe(labels.nth(i), f"LABEL {i + 1}")

        controls = page.locator(
            "input, button, [role='switch'], [role='checkbox'], "
            "[aria-checked], [data-p-checked]"
        )

        relevant = []

        for i in range(controls.count()):
            node = controls.nth(i)

            try:
                text = clean(node.inner_text())
            except Exception:
                text = ""

            try:
                aria = clean(node.get_attribute("aria-label"))
            except Exception:
                aria = ""

            hay = f"{text} {aria}".casefold()

            if "induló" in hay or "befizetés" in hay:
                relevant.append(node)

        print("\nRelevant explicit controls:", len(relevant))

        for i, node in enumerate(relevant):
            describe(node, f"CONTROL {i + 1}")

        # ----------------------------------------------------
        # Parent chain around label
        # ----------------------------------------------------
        if labels.count():
            current = labels.first

            print("\n--- LABEL PARENT CHAIN ---")

            for level in range(8):
                describe(current, f"PARENT LEVEL {level}")

                try:
                    parent = current.locator("xpath=..")
                    if not parent.count():
                        break
                    current = parent
                except Exception:
                    break

        # ----------------------------------------------------
        # Initial state
        # ----------------------------------------------------
        state_snapshot(
            page,
            "INITIAL STATE",
        )

        # ----------------------------------------------------
        # Find likely switch by proximity, not by assumption
        # ----------------------------------------------------
        switch = None

        # 1. direct role switch
        role_switch = page.get_by_role("switch")
        for i in range(role_switch.count()):
            node = role_switch.nth(i)

            try:
                parent_text = clean(
                    node.locator("xpath=..").inner_text()
                )
            except Exception:
                parent_text = ""

            if LABEL.casefold() in parent_text.casefold():
                switch = node
                break

        # 2. checkbox near label
        if switch is None and labels.count():
            label = labels.first

            for xpath in (
                "xpath=../input",
                "xpath=../button",
                "xpath=..//*[@role='switch']",
                "xpath=..//*[@role='checkbox']",
                "xpath=..//input[@type='checkbox']",
                "xpath=../..//*[@role='switch']",
                "xpath=../..//input[@type='checkbox']",
                "xpath=../../..//*[@role='switch']",
                "xpath=../../..//input[@type='checkbox']",
            ):
                loc = label.locator(xpath)

                for i in range(loc.count()):
                    node = loc.nth(i)

                    try:
                        if node.is_visible():
                            switch = node
                            break
                    except Exception:
                        continue

                if switch is not None:
                    break

        if switch is None:
            print(
                "\nNO SWITCH RESOLVED. "
                "Diagnostic completed without changing page state."
            )
            browser.close()
            return

        describe(switch, "RESOLVED SWITCH BEFORE CLICK")

        # ----------------------------------------------------
        # Toggle once and inspect observed price change
        # ----------------------------------------------------
        before = visible_fee_texts(page)

        try:
            switch.click(timeout=5000)
            page.wait_for_timeout(1800)
        except Exception as exc:
            print("\nSWITCH CLICK FAILED:", exc)
            browser.close()
            return

        describe(switch, "RESOLVED SWITCH AFTER CLICK")

        after = visible_fee_texts(page)

        state_snapshot(
            page,
            "STATE AFTER ONE TOGGLE",
        )

        print("\n--- PRICE-LIKE TEXT DELTA ---")
        print("BEFORE:")
        for value in before[:30]:
            print("-", value)

        print("\nAFTER:")
        for value in after[:30]:
            print("-", value)

        print(
            "\nDIAGNOSTIC COMPLETE. "
            "NO DOWN-PAYMENT SEMANTICS WERE INFERRED FROM SWITCH STATE."
        )

        browser.close()


if __name__ == "__main__":
    main()
