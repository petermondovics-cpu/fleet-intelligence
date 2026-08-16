from playwright.sync_api import sync_playwright


ARVAL_URL = (
    "https://www.arval.hu/"
    "kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/"
    "byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)

AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)


KEYWORDS = [
    "felszereltség",
    "alapfelszereltség",
    "opcionális",
    "extra",
    "biztosítás",
    "casco",
    "kötelező",
    "szerviz",
    "karbantartás",
    "gumi",
    "abroncs",
    "assistance",
    "segély",
    "üzemanyagkártya",
    "üzemanyag kártya",
    "csereautó",
    "önerő",
    "kezdőrészlet",
    "induló díj",
    "induló befizetés",
    "első díj",
    "flottakezelés",
]


def dismiss_generic_cookies(page):
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
            locator.first.click(timeout=2500)
            page.wait_for_timeout(400)
            return
        except Exception:
            continue


def normalize(text):
    return (
        text.lower()
        .replace("\xa0", " ")
        .strip()
    )


def print_match_details(item, keyword, index):
    print("\n" + "-" * 88)
    print(
        f"MATCH {index} | KEYWORD: {keyword}"
    )
    print("-" * 88)

    try:
        text = item.inner_text().strip()
    except Exception:
        text = ""

    print(
        "TEXT:",
        repr(text[:1800]),
    )

    try:
        data = item.evaluate(
            """
            (el) => {
                const attrs = {};
                for (const a of el.attributes || []) {
                    attrs[a.name] = a.value;
                }

                return {
                    tag: el.tagName,
                    id: el.id || null,
                    className: el.className || null,
                    role: el.getAttribute('role'),
                    attrs,
                    outerHTML: el.outerHTML.slice(0, 8000)
                };
            }
            """
        )

        print("TAG:", data["tag"])
        print("ID:", data["id"])
        print("ROLE:", data["role"])
        print("CLASS:", data["className"])
        print("ATTRS:", data["attrs"])
        print("OUTER HTML:")
        print(data["outerHTML"])

    except Exception as exc:
        print("DETAIL ERROR:", exc)

    try:
        tree = item.evaluate(
            """
            (el) => {
                const result = [];
                let current = el;

                for (let i = 0; i < 7 && current; i++) {
                    result.push({
                        level: i,
                        tag: current.tagName,
                        id: current.id || null,
                        className: current.className || null,
                        role: current.getAttribute('role'),
                        text: (current.innerText || '').slice(0, 1800),
                        outerHTML: current.outerHTML.slice(0, 5000)
                    });

                    current = current.parentElement;
                }

                return result;
            }
            """
        )

        print("ANCESTOR TREE:")

        for node in tree:
            print(
                f"LEVEL {node['level']} | "
                f"{node['tag']} | "
                f"id={node['id']} | "
                f"role={node['role']} | "
                f"class={node['className']}"
            )
            print(
                repr(node["text"][:800])
            )

    except Exception as exc:
        print(
            "ANCESTOR TREE ERROR:",
            exc,
        )


def inspect_keyword_matches(
    page,
    provider,
):
    print("\n" + "=" * 88)
    print(
        f"{provider.upper()} KEYWORD DOM MATCHES"
    )
    print("=" * 88)

    candidates = page.locator(
        "h1, h2, h3, h4, h5, h6, "
        "p, span, div, li, ul, ol, "
        "section, article, "
        "button, label, strong, b, "
        "dt, dd, table, tr, td, th, "
        "input, select, option, a"
    )

    found = 0
    seen = set()

    for i in range(
        candidates.count()
    ):
        item = candidates.nth(i)

        try:
            if not item.is_visible():
                continue

            text = (
                item.inner_text()
                .strip()
            )

        except Exception:
            continue

        if not text:
            continue

        normalized = normalize(text)

        matched_keyword = None

        for keyword in KEYWORDS:
            if keyword in normalized:
                matched_keyword = keyword
                break

        if matched_keyword is None:
            continue

        fingerprint = (
            matched_keyword,
            text[:300],
        )

        if fingerprint in seen:
            continue

        seen.add(fingerprint)
        found += 1

        print_match_details(
            item,
            matched_keyword,
            found,
        )

        if found >= 60:
            print(
                "\nStopped after 60 matches "
                "to keep the diagnostic readable."
            )
            break

    print(
        f"\nTOTAL KEYWORD MATCHES: {found}"
    )


def inspect_candidate_sections(
    page,
    provider,
):
    print("\n" + "=" * 88)
    print(
        f"{provider.upper()} CANDIDATE DETAIL SECTIONS"
    )
    print("=" * 88)

    selectors = [
        "section",
        "article",
        "div[class*='equipment']",
        "div[class*='Equipment']",
        "div[class*='service']",
        "div[class*='Service']",
        "div[class*='feature']",
        "div[class*='Feature']",
        "div[class*='benefit']",
        "div[class*='Benefit']",
        "div[class*='insurance']",
        "div[class*='Insurance']",
        "div[class*='detail']",
        "div[class*='Detail']",
        "div[class*='spec']",
        "div[class*='Spec']",
    ]

    printed = 0
    seen_html = set()

    for selector in selectors:
        blocks = page.locator(selector)

        for i in range(
            blocks.count()
        ):
            block = blocks.nth(i)

            try:
                if not block.is_visible():
                    continue

                text = (
                    block.inner_text()
                    .strip()
                )

            except Exception:
                continue

            if len(text) < 20:
                continue

            normalized = normalize(text)

            if not any(
                keyword in normalized
                for keyword in KEYWORDS
            ):
                continue

            try:
                html = block.evaluate(
                    "(el) => el.outerHTML"
                )
            except Exception:
                continue

            html_key = html[:600]

            if html_key in seen_html:
                continue

            seen_html.add(html_key)

            printed += 1

            print(
                "\n"
                + "-" * 88
            )

            print(
                f"SECTION {printed} | "
                f"SELECTOR: {selector}"
            )

            print(
                "-" * 88
            )

            print(
                "TEXT:",
                repr(text[:3000]),
            )

            print(
                "HTML:",
                html[:12000],
            )

            if printed >= 20:
                print(
                    "\nStopped after 20 sections."
                )
                return

    print(
        f"\nTOTAL CANDIDATE SECTIONS: "
        f"{printed}"
    )


def inspect_metadata(
    page,
    provider,
):
    print("\n" + "=" * 88)
    print(
        f"{provider.upper()} PAGE METADATA"
    )
    print("=" * 88)

    print(
        "TITLE:",
        page.title(),
    )

    print(
        "URL:",
        page.url,
    )

    scripts = page.locator(
        "script[type='application/ld+json']"
    )

    print(
        "LD+JSON COUNT:",
        scripts.count(),
    )

    for i in range(
        min(
            scripts.count(),
            10,
        )
    ):
        try:
            text = (
                scripts.nth(i)
                .inner_text()
                .strip()
            )
        except Exception:
            continue

        print(
            f"\nLD+JSON {i + 1}:"
        )
        print(
            text[:10000]
        )


def run_provider(
    page,
    provider,
    url,
):
    print(
        "\n\n"
        + "#" * 88
    )

    print(
        f"{provider.upper()} OFFER DETAIL DIAGNOSTIC"
    )

    print(
        "#" * 88
    )

    page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=60000,
    )

    page.wait_for_timeout(
        3000
    )

    dismiss_generic_cookies(
        page
    )

    page.wait_for_timeout(
        800
    )

    inspect_metadata(
        page,
        provider,
    )

    inspect_keyword_matches(
        page,
        provider,
    )

    inspect_candidate_sections(
        page,
        provider,
    )


def main():

    print(
        "\n"
        + "=" * 88
    )

    print(
        "FLEETIQ OFFER DETAILS DOM DIAGNOSTIC V1"
    )

    print(
        "=" * 88
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        run_provider(
            page,
            "Arval",
            ARVAL_URL,
        )

        run_provider(
            page,
            "Ayvens",
            AYVENS_URL,
        )

        input(
            "\nPress ENTER to close browser..."
        )

        browser.close()


if __name__ == "__main__":
    main()
