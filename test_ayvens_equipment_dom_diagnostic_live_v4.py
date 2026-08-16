from playwright.sync_api import sync_playwright


URL = "https://autotartosberlet.ayvens.com/byd/atto-2-dm-i"
LABEL = "Alapfelszereltség"


def clean(value):
    return " ".join((value or "").split())


def safe_attr(node, name):
    try:
        return node.get_attribute(name)
    except Exception:
        return None


def safe_text(node):
    try:
        return clean(node.inner_text())
    except Exception:
        return ""


def visible(node):
    try:
        return node.is_visible()
    except Exception:
        return False


def dismiss_cookies(page):
    selectors = (
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
    )

    for selector in selectors:
        loc = page.locator(selector)
        if not loc.count():
            continue
        try:
            loc.first.click(timeout=2000)
            page.wait_for_timeout(400)
            return
        except Exception:
            pass


def describe(node, prefix=""):
    try:
        tag = node.evaluate("(el) => el.tagName")
    except Exception:
        tag = "?"

    print(
        prefix,
        "tag=", tag,
        "| visible=", visible(node),
        "| role=", safe_attr(node, "role"),
        "| id=", safe_attr(node, "id"),
        "| class=", safe_attr(node, "class"),
        "| aria-controls=", safe_attr(node, "aria-controls"),
        "| aria-selected=", safe_attr(node, "aria-selected"),
        "| aria-expanded=", safe_attr(node, "aria-expanded"),
    )
    text = safe_text(node)
    if text:
        print(prefix, "text:", text[:500])


def main():
    print("=" * 90)
    print("AYVENS ATTO 2 EQUIPMENT DOM DIAGNOSTIC LIVE V4")
    print("=" * 90)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(
            URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_timeout(3000)
        dismiss_cookies(page)

        print("\nURL:", page.url)

        # ----------------------------------------------------
        # 1. Exact label matches
        # ----------------------------------------------------
        print("\n--- 1. EXACT LABEL MATCHES ---")

        matches = page.get_by_text(
            LABEL,
            exact=True,
        )

        print("Count:", matches.count())

        for i in range(matches.count()):
            node = matches.nth(i)
            print(f"\nMATCH {i + 1}")
            describe(node, " ")

        # ----------------------------------------------------
        # 2. Role-based controls
        # ----------------------------------------------------
        print("\n--- 2. ROLE / CONTROL MATCHES ---")

        selectors = (
            "[role='tab']",
            "button",
            "[aria-controls]",
            "[aria-expanded]",
        )

        for selector in selectors:
            nodes = page.locator(selector)
            hits = []

            for i in range(nodes.count()):
                node = nodes.nth(i)
                text = safe_text(node)
                if LABEL.casefold() in text.casefold():
                    hits.append(node)

            print(f"\nSelector {selector}: {len(hits)} relevant")

            for node in hits[:10]:
                describe(node, " ")

        # ----------------------------------------------------
        # 3. Parent chain
        # ----------------------------------------------------
        print("\n--- 3. PARENT CHAIN ---")

        if matches.count():
            current = matches.last

            for level in range(10):
                print(f"\nLEVEL {level}")
                describe(current, " ")

                try:
                    parent = current.locator("xpath=..")
                    if not parent.count():
                        break
                    current = parent
                except Exception:
                    break

        # ----------------------------------------------------
        # 4. Siblings around exact heading
        # ----------------------------------------------------
        print("\n--- 4. NEARBY SIBLINGS ---")

        if matches.count():
            node = matches.last

            for relation, xpath in (
                ("previous", "xpath=preceding-sibling::*[1]"),
                ("next", "xpath=following-sibling::*[1]"),
                ("next-2", "xpath=following-sibling::*[2]"),
                ("parent-next", "xpath=../following-sibling::*[1]"),
                ("parent-next-2", "xpath=../following-sibling::*[2]"),
            ):
                try:
                    loc = node.locator(xpath)
                    print(f"\n{relation}: count={loc.count()}")
                    if loc.count():
                        describe(loc.first, " ")
                except Exception as exc:
                    print(relation, "ERROR:", exc)

        # ----------------------------------------------------
        # 5. Candidate containers containing label
        # ----------------------------------------------------
        print("\n--- 5. CANDIDATE CONTAINERS ---")

        candidates = page.locator(
            "section, article, [role='tabpanel'], "
            "[class*='tab'], [class*='accordion'], "
            "[class*='equipment'], [class*='feature'], "
            "[class*='spec']"
        )

        rows = []

        for i in range(candidates.count()):
            node = candidates.nth(i)
            text = safe_text(node)

            if LABEL.casefold() not in text.casefold():
                continue

            rows.append(
                (
                    len(text),
                    i,
                    node,
                    text,
                )
            )

        rows.sort(
            key=lambda x: x[0]
        )

        print("Relevant candidate containers:", len(rows))

        for length, index, node, text in rows[:20]:
            print(
                f"\nindex={index} | text_length={length}"
            )
            describe(node, " ")
            print(" preview:", text[:1200])

        # ----------------------------------------------------
        # 6. DOM text around heading using JS
        # ----------------------------------------------------
        print("\n--- 6. DOM NEIGHBORHOOD SNAPSHOT ---")

        if matches.count():
            node = matches.last

            snapshot = node.evaluate(
                """
                el => {
                    const out = [];
                    let cur = el;

                    for (let level = 0; level < 6 && cur; level++) {
                        const parent = cur.parentElement;
                        if (!parent) break;

                        out.push({
                            level,
                            parentTag: parent.tagName,
                            parentClass: parent.className,
                            parentText: (parent.innerText || '').slice(0, 3000),
                            children: Array.from(parent.children).map((x, i) => ({
                                i,
                                tag: x.tagName,
                                cls: x.className,
                                role: x.getAttribute('role'),
                                ariaControls: x.getAttribute('aria-controls'),
                                ariaExpanded: x.getAttribute('aria-expanded'),
                                text: (x.innerText || '').slice(0, 1200)
                            }))
                        });

                        cur = parent;
                    }

                    return out;
                }
                """
            )

            for block in snapshot:
                print(
                    "\nLEVEL",
                    block["level"],
                    "| parentTag=",
                    block["parentTag"],
                    "| class=",
                    block["parentClass"],
                )
                print(
                    "PARENT TEXT:",
                    clean(block["parentText"])[:1500],
                )

                for child in block["children"]:
                    print(
                        " CHILD",
                        child["i"],
                        "|",
                        child["tag"],
                        "| role=",
                        child["role"],
                        "| aria-controls=",
                        child["ariaControls"],
                        "| aria-expanded=",
                        child["ariaExpanded"],
                    )
                    print(
                        "   ",
                        clean(child["text"])[:700],
                    )

        # ----------------------------------------------------
        # 7. Search for likely equipment leaf nodes globally
        # ----------------------------------------------------
        print("\n--- 7. VISIBLE LEAF TEXT NEAR EQUIPMENT AREA ---")

        leafs = page.locator(
            "li, [role='listitem'], p, span"
        )

        interesting = []

        for i in range(leafs.count()):
            node = leafs.nth(i)

            if not visible(node):
                continue

            text = safe_text(node)

            if not text or len(text) > 220:
                continue

            lowered = text.casefold()

            # Diagnostic only: deliberately broad terms.
            if any(
                term in lowered
                for term in (
                    "kamera",
                    "ülés",
                    "kormány",
                    "carplay",
                    "android",
                    "fényszór",
                    "parkol",
                    "tető",
                    "ablak",
                    "tölt",
                    "érintő",
                    "hangszór",
                )
            ):
                interesting.append(
                    (i, node, text)
                )

        print("Interesting visible leaf nodes:", len(interesting))

        for i, node, text in interesting[:80]:
            print(f"\nleaf index={i}")
            describe(node, " ")
            print(" candidate text:", text)

        print(
            "\nDIAGNOSTIC COMPLETE - NO EQUIPMENT CLASSIFICATION "
            "OR EVIDENCE STATUS WAS CHANGED."
        )

        browser.close()


if __name__ == "__main__":
    main()
