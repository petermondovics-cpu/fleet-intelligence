import json
import re

from playwright.sync_api import sync_playwright


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajandlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)


ACTION_TEXT = "AJÁNLAT KIVÁLASZTÁSA"


FINANCIAL_PATTERN = re.compile(
    r"(?i)"
    r"(önerő|kezdeti befizetés|kezdő befizetés|"
    r"induló befizetés|első befizetés|előleg|kaució|"
    r"depozit|down payment|initial payment|advance payment|"
    r"\b0\s*%|\b10\s*%|\b20\s*%|\b30\s*%)"
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

        if not loc.count():
            continue

        try:
            loc.first.click(
                timeout=1500
            )
            page.wait_for_timeout(
                250
            )
            return
        except Exception:
            pass


def normalize(text):
    return " ".join(
        (text or "").split()
    )


def attrs(locator):
    return locator.evaluate(
        """
        el => {
            const out = {
                tag: el.tagName,
                id: el.id || null,
                class: el.className || null,
                role: el.getAttribute('role'),
                href: el.getAttribute('href'),
                type: el.getAttribute('type'),
                name: el.getAttribute('name'),
                value: el.getAttribute('value'),
                onclick: el.getAttribute('onclick'),
                ariaLabel: el.getAttribute('aria-label'),
                dataTestId: el.getAttribute('data-testid'),
                dataDrupalSelector: el.getAttribute('data-drupal-selector'),
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
        return normalize(
            locator.inner_text()
        )
    except Exception:
        return ""


def print_financial_state(
    page,
    title,
):
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)

    print(
        "URL:",
        page.url,
    )

    try:
        print(
            "TITLE:",
            page.title(),
        )
    except Exception:
        pass

    body = (
        page.locator("body")
        .inner_text()
    )

    lower = body.casefold()

    print()
    print("--- FINANCIAL KEYWORD HITS ---")

    hit_count = 0

    keywords = (
        "önerő",
        "kezdő befizetés",
        "kezdeti befizetés",
        "induló befizetés",
        "első befizetés",
        "előleg",
        "kaució",
        "depozit",
        "down payment",
        "initial payment",
        "0%",
        "10%",
        "20%",
        "30%",
    )

    for keyword in keywords:
        pos = lower.find(
            keyword.casefold()
        )

        if pos < 0:
            continue

        hit_count += 1

        lo = max(
            0,
            pos - 300,
        )

        hi = min(
            len(body),
            pos + len(keyword) + 700,
        )

        print()
        print(
            "KEYWORD:",
            keyword,
        )
        print(
            normalize(
                body[lo:hi]
            )
        )

    if hit_count == 0:
        print(
            "No financial keyword hits."
        )

    print()
    print("--- FINANCIAL-LIKE DOM ELEMENTS ---")

    nodes = page.locator(
        "input, select, option, label, button, a, "
        "p, span, div, form, fieldset, legend"
    )

    emitted = 0

    for i in range(
        nodes.count()
    ):
        node = nodes.nth(i)

        try:
            text = safe_text(
                node
            )

            meta = attrs(
                node
            )
        except Exception:
            continue

        blob = (
            text
            + " "
            + json.dumps(
                meta,
                ensure_ascii=False,
            )
        )

        if not FINANCIAL_PATTERN.search(
            blob
        ):
            continue

        emitted += 1

        print()
        print(
            f"FINANCIAL ELEMENT {emitted}"
        )
        print(
            "attrs:",
            meta,
        )
        print(
            "text:",
            text[:2500],
        )

        if emitted >= 80:
            break

    if emitted == 0:
        print(
            "No financial-like DOM elements."
        )


def collect_action_candidates(page):
    """
    V2 does not rely on one semantic locator.

    It searches:
    1. any DOM element whose own visible text equals/contains action text;
    2. closest clickable ancestor;
    3. descendants inside wrappers whose text contains action text;
    4. raw anchors/buttons with common offer CTA attributes/classes.

    Returns unique clickable locator candidates with diagnostics.
    """

    result = []
    seen_handles = set()

    all_nodes = page.locator(
        "a, button, span, div, p, input, label"
    )

    for i in range(
        all_nodes.count()
    ):
        node = all_nodes.nth(i)

        try:
            if not node.is_visible():
                continue

            text = safe_text(
                node
            )
        except Exception:
            continue

        if (
            ACTION_TEXT.casefold()
            not in text.casefold()
        ):
            continue

        # Avoid huge page wrappers unless used only to inspect descendants.
        if len(text) > 600:
            continue

        try:
            info = node.evaluate(
                """
                el => {
                    const clickable = el.closest(
                        'a,button,[role="button"],input[type="submit"],input[type="button"]'
                    );

                    const target = clickable || el;

                    return {
                        tag: target.tagName,
                        text: (target.innerText || target.value || '').trim(),
                        id: target.id || null,
                        class: target.className || null,
                        href: target.getAttribute('href'),
                        role: target.getAttribute('role'),
                        type: target.getAttribute('type'),
                        onclick: target.getAttribute('onclick'),
                        outerHTML: target.outerHTML.slice(0, 2500),
                    };
                }
                """
            )
        except Exception:
            continue

        selector_hint = (
            info.get("id"),
            info.get("href"),
            info.get("class"),
            info.get("outerHTML"),
        )

        key = str(
            selector_hint
        )

        if key in seen_handles:
            continue

        seen_handles.add(
            key
        )

        result.append(
            (
                node,
                info,
            )
        )

    # Direct CTA-ish elements even if inner_text is carried by a child.
    ctas = page.locator(
        "a, button, [role='button'], input[type='submit'], input[type='button']"
    )

    for i in range(
        ctas.count()
    ):
        node = ctas.nth(i)

        try:
            if not node.is_visible():
                continue

            text = safe_text(
                node
            )

            value = (
                node.get_attribute(
                    "value"
                )
                or ""
            )

            meta = attrs(
                node
            )
        except Exception:
            continue

        blob = (
            text
            + " "
            + value
            + " "
            + json.dumps(
                meta,
                ensure_ascii=False,
            )
        )

        if (
            "ajánlat"
            not in blob.casefold()
            and "offer"
            not in blob.casefold()
        ):
            continue

        try:
            info = {
                "tag": meta.get("tag"),
                "text": text or value,
                "id": meta.get("id"),
                "class": meta.get("class"),
                "href": meta.get("href"),
                "role": meta.get("role"),
                "type": meta.get("type"),
                "onclick": meta.get("onclick"),
                "outerHTML": node.evaluate(
                    "el => el.outerHTML.slice(0, 2500)"
                ),
            }
        except Exception:
            continue

        key = str(
            (
                info.get("id"),
                info.get("href"),
                info.get("class"),
                info.get("outerHTML"),
            )
        )

        if key in seen_handles:
            continue

        seen_handles.add(
            key
        )

        result.append(
            (
                node,
                info,
            )
        )

    return result


def click_candidate(page, node):
    """
    Click nearest clickable ancestor if present.
    No form submission is performed after the CTA transition.
    """

    try:
        clickable = node.locator(
            "xpath=ancestor-or-self::a | "
            "ancestor-or-self::button | "
            "ancestor-or-self::*[@role='button'] | "
            "ancestor-or-self::input[@type='submit'] | "
            "ancestor-or-self::input[@type='button']"
        )

        if clickable.count():
            clickable.first.click(
                timeout=4000
            )
            return True
    except Exception:
        pass

    try:
        node.click(
            timeout=4000
        )
        return True
    except Exception:
        return False


def print_forms(page):
    print()
    print("--- FORMS / FIELDS AFTER ACTION ---")

    forms = page.locator(
        "form"
    )

    print(
        "Form count:",
        forms.count(),
    )

    for i in range(
        min(
            forms.count(),
            20,
        )
    ):
        form = forms.nth(i)

        print()
        print(
            f"FORM {i + 1}"
        )

        try:
            print(
                "attrs:",
                attrs(
                    form
                ),
            )
            print(
                "text:",
                safe_text(
                    form
                )[:3500],
            )
        except Exception:
            pass

        fields = form.locator(
            "input, select, option, textarea, button, label"
        )

        for j in range(
            min(
                fields.count(),
                100,
            )
        ):
            field = fields.nth(j)

            try:
                print(
                    "  FIELD:",
                    attrs(
                        field
                    ),
                    "| text:",
                    safe_text(
                        field
                    )[:800],
                )
            except Exception:
                continue


def main():
    print("=" * 100)
    print("ARVAL EXACT-OFFER QUOTE FLOW FINANCIAL DIAGNOSTIC V2")
    print("=" * 100)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        try:
            context = browser.new_context()

            popup_pages = []
            requests = []

            context.on(
                "page",
                lambda pg: popup_pages.append(
                    pg
                ),
            )

            page = context.new_page()

            page.on(
                "request",
                lambda req: requests.append(
                    {
                        "method": req.method,
                        "resource_type": req.resource_type,
                        "url": req.url,
                        "post_data": (
                            req.post_data
                            if req.method != "GET"
                            else None
                        ),
                    }
                ),
            )

            page.goto(
                ARVAL_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            page.wait_for_timeout(
                2000
            )

            dismiss(
                page
            )

            print_financial_state(
                page,
                "STEP 1 - EXACT OFFER BEFORE ACTION",
            )

            print()
            print("--- RAW ACTION TEXT CHECK ---")

            body_text = (
                page.locator("body")
                .inner_text()
            )

            print(
                "Body contains CTA:",
                ACTION_TEXT.casefold()
                in body_text.casefold(),
            )

            if (
                ACTION_TEXT.casefold()
                in body_text.casefold()
            ):
                pos = (
                    body_text.casefold()
                    .find(
                        ACTION_TEXT.casefold()
                    )
                )

                print(
                    normalize(
                        body_text[
                            max(0, pos - 500):
                            min(
                                len(body_text),
                                pos + 1200,
                            )
                        ]
                    )
                )

            print()
            print("--- ACTION CANDIDATES V2 ---")

            actions = collect_action_candidates(
                page
            )

            print(
                "Count:",
                len(actions),
            )

            for idx, (
                _,
                info,
            ) in enumerate(
                actions,
                start=1,
            ):
                print()
                print(
                    f"ACTION {idx}"
                )

                for key in (
                    "tag",
                    "text",
                    "id",
                    "class",
                    "href",
                    "role",
                    "type",
                    "onclick",
                    "outerHTML",
                ):
                    print(
                        f"{key}:",
                        info.get(
                            key
                        ),
                    )

            if not actions:
                print()
                print(
                    "CTA text exists only in ancestor/body text, but no "
                    "clickable DOM candidate was safely identified."
                )

                print()
                print(
                    "DIAGNOSTIC COMPLETE - NO CLICK ATTEMPTED."
                )
                return

            print()
            print("--- CLICKING BEST CTA CANDIDATE ---")

            target, info = actions[0]

            print(
                "Chosen:",
                info,
            )

            popup_count_before = len(
                popup_pages
            )

            old_url = page.url

            clicked = click_candidate(
                page,
                target,
            )

            print(
                "Click success:",
                clicked,
            )

            if not clicked:
                print(
                    "No unsafe JS-forced click fallback was attempted."
                )
                return

            page.wait_for_timeout(
                2200
            )

            active_page = page

            if (
                len(popup_pages)
                > popup_count_before
            ):
                active_page = (
                    popup_pages[-1]
                )

                try:
                    active_page.wait_for_load_state(
                        "domcontentloaded",
                        timeout=15000,
                    )
                except Exception:
                    pass

                active_page.wait_for_timeout(
                    1200
                )

            print()
            print(
                "URL before:",
                old_url,
            )
            print(
                "URL after:",
                active_page.url,
            )

            print_financial_state(
                active_page,
                "STEP 2 - AFTER EXACT OFFER ACTION",
            )

            print_forms(
                active_page
            )

            print()
            print("--- RELEVANT NETWORK REQUESTS ---")

            tokens = (
                "offer",
                "quote",
                "lead",
                "form",
                "contact",
                "request",
                "proposal",
                "finance",
                "payment",
                "leasing",
                "api",
                "ajax",
            )

            for item in requests:
                if not any(
                    token in item[
                        "url"
                    ].casefold()
                    for token in tokens
                ):
                    continue

                print(
                    json.dumps(
                        item,
                        ensure_ascii=False,
                    )[:6000]
                )

            print()
            print("=" * 100)
            print(
                "DIAGNOSTIC COMPLETE - ONLY THE OFFER-SELECTION CTA "
                "WAS CLICKED. NO FORM WAS SUBMITTED, NO PERSONAL DATA "
                "WAS ENTERED, AND NO DOWN-PAYMENT CONDITION WAS "
                "INFERRED FROM ABSENCE."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
