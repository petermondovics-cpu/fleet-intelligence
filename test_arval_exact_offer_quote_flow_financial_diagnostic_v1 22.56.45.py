import json
import re
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajandlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)


FINANCIAL_KEYWORDS = (
    "önerő",
    "kezdeti befizetés",
    "kezdő befizetés",
    "induló befizetés",
    "első befizetés",
    "kezdőrészlet",
    "kezdő részlet",
    "előleg",
    "kaució",
    "depozit",
    "down payment",
    "initial payment",
    "advance payment",
    "0%",
    "10%",
    "20%",
    "30%",
)


BUTTON_LABELS = (
    "AJÁNLAT KIVÁLASZTÁSA",
    "Ajánlat kiválasztása",
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
            loc.first.click(timeout=1500)
            page.wait_for_timeout(250)
            return
        except Exception:
            pass


def normalize_text(text):
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
                action: el.getAttribute('action'),
                method: el.getAttribute('method'),
                type: el.getAttribute('type'),
                name: el.getAttribute('name'),
                value: el.getAttribute('value'),
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
        return normalize_text(
            locator.inner_text()
        )
    except Exception:
        return ""


def body_keyword_hits(page):
    body = page.locator(
        "body"
    ).inner_text()

    lower = body.casefold()

    hits = []

    for keyword in FINANCIAL_KEYWORDS:
        start = 0
        count = 0

        while True:
            idx = lower.find(
                keyword.casefold(),
                start,
            )

            if idx < 0:
                break

            count += 1

            lo = max(
                0,
                idx - 220,
            )

            hi = min(
                len(body),
                idx + len(keyword) + 420,
            )

            hits.append(
                (
                    keyword,
                    normalize_text(
                        body[lo:hi]
                    ),
                )
            )

            start = (
                idx + len(keyword)
            )

            if count >= 5:
                break

    return hits


def financial_elements(page):
    pattern = re.compile(
        r"(?i)"
        r"(önerő|kezdeti befizetés|kezdő befizetés|"
        r"induló befizetés|első befizetés|előleg|kaució|"
        r"depozit|down payment|initial payment|advance payment|"
        r"\b0\s*%|\b10\s*%|\b20\s*%|\b30\s*%)"
    )

    selectors = (
        "label, input, select, option, button, a, p, span, div, "
        "strong, b, h1, h2, h3, h4, form, fieldset, legend"
    )

    loc = page.locator(
        selectors
    )

    rows = []
    seen = set()

    for i in range(
        loc.count()
    ):
        item = loc.nth(i)

        try:
            text = safe_text(
                item
            )
            meta = attrs(
                item
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

        if not pattern.search(
            blob
        ):
            continue

        key = (
            text,
            str(meta),
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        rows.append(
            (
                item,
                text,
                meta,
            )
        )

    return rows[:100]


def print_current_state(
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

    print()
    print("--- FINANCIAL KEYWORD HITS ---")

    hits = body_keyword_hits(
        page
    )

    if not hits:
        print(
            "No financial keyword hits."
        )

    for keyword, context in hits:
        print()
        print(
            "KEYWORD:",
            keyword,
        )
        print(
            context
        )

    print()
    print("--- FINANCIAL-LIKE ELEMENTS ---")

    rows = financial_elements(
        page
    )

    if not rows:
        print(
            "No financial-like DOM elements."
        )

    for idx, (
        item,
        text,
        meta,
    ) in enumerate(
        rows,
        start=1,
    ):
        print()
        print(
            f"ELEMENT {idx}"
        )
        print(
            "attrs:",
            meta,
        )
        print(
            "text:",
            text[:1800],
        )

        try:
            parent = item.locator(
                ".."
            )
            print(
                "parent attrs:",
                attrs(parent),
            )
            print(
                "parent text:",
                safe_text(
                    parent
                )[:2200],
            )
        except Exception:
            pass


def find_offer_actions(page):
    actions = []

    # Explicit visible text first.
    for label in BUTTON_LABELS:
        candidates = page.get_by_text(
            label,
            exact=True,
        )

        for i in range(
            candidates.count()
        ):
            loc = candidates.nth(i)

            try:
                if not loc.is_visible():
                    continue
                meta = attrs(
                    loc
                )
                text = safe_text(
                    loc
                )
            except Exception:
                continue

            actions.append(
                (
                    loc,
                    text,
                    meta,
                )
            )

    # Then inspect controls whose text contains the label.
    controls = page.locator(
        "a, button, input[type='submit'], input[type='button']"
    )

    for i in range(
        controls.count()
    ):
        loc = controls.nth(i)

        try:
            if not loc.is_visible():
                continue

            text = safe_text(
                loc
            )

            if not text:
                value = (
                    loc.get_attribute(
                        "value"
                    )
                    or ""
                )
                text = normalize_text(
                    value
                )

            if (
                "ajánlat kiválasztása"
                not in text.casefold()
            ):
                continue

            meta = attrs(
                loc
            )
        except Exception:
            continue

        actions.append(
            (
                loc,
                text,
                meta,
            )
        )

    # Deduplicate by DOM metadata + text.
    out = []
    seen = set()

    for item in actions:
        _, text, meta = item
        key = (
            text,
            str(meta),
        )

        if key in seen:
            continue

        seen.add(
            key
        )
        out.append(
            item
        )

    return out


def main():
    print("=" * 100)
    print("ARVAL EXACT-OFFER QUOTE FLOW FINANCIAL DIAGNOSTIC V1")
    print("=" * 100)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        try:
            context = browser.new_context()

            requests = []
            responses = []
            popups = []

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

            page.on(
                "response",
                lambda resp: responses.append(
                    {
                        "status": resp.status,
                        "url": resp.url,
                    }
                ),
            )

            context.on(
                "page",
                lambda new_page: popups.append(
                    new_page
                ),
            )

            page.goto(
                ARVAL_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            page.wait_for_timeout(
                1800
            )

            dismiss(
                page
            )

            print_current_state(
                page,
                "STEP 1 - EXACT OFFER BEFORE ACTION",
            )

            actions = find_offer_actions(
                page
            )

            print()
            print("--- OFFER ACTION CANDIDATES ---")
            print(
                "Count:",
                len(actions),
            )

            for idx, (
                _,
                text,
                meta,
            ) in enumerate(
                actions,
                start=1,
            ):
                print()
                print(
                    f"ACTION {idx}"
                )
                print(
                    "text:",
                    text,
                )
                print(
                    "attrs:",
                    meta,
                )

                href = (
                    meta.get(
                        "href"
                    )
                    if isinstance(
                        meta,
                        dict,
                    )
                    else None
                )

                if href:
                    print(
                        "resolved href:",
                        urljoin(
                            page.url,
                            href,
                        ),
                    )

            if not actions:
                print()
                print(
                    "No safely identifiable 'AJÁNLAT KIVÁLASZTÁSA' "
                    "action found. No click attempted."
                )
                return

            target, _, target_meta = (
                actions[0]
            )

            print()
            print("--- CLICKING FIRST EXACT OFFER ACTION ---")
            print(
                "Target attrs:",
                target_meta,
            )

            before_url = page.url
            popup_before = len(
                popups
            )

            try:
                target.click(
                    timeout=3000
                )
            except Exception as exc:
                print(
                    "Click failed:",
                    repr(exc),
                )
                return

            page.wait_for_timeout(
                1800
            )

            active_page = page

            if len(
                popups
            ) > popup_before:
                active_page = (
                    popups[-1]
                )

                try:
                    active_page.wait_for_load_state(
                        "domcontentloaded",
                        timeout=15000,
                    )
                except Exception:
                    pass

                active_page.wait_for_timeout(
                    1000
                )

            print()
            print(
                "Original URL:",
                before_url,
            )
            print(
                "Active URL after click:",
                active_page.url,
            )

            print_current_state(
                active_page,
                "STEP 2 - AFTER EXACT OFFER ACTION",
            )

            print()
            print("--- FORMS AFTER ACTION ---")

            forms = active_page.locator(
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
                form = forms.nth(
                    i
                )

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
                    "input, select, textarea, button"
                )

                for j in range(
                    min(
                        fields.count(),
                        80,
                    )
                ):
                    field = fields.nth(
                        j
                    )

                    try:
                        print(
                            "  FIELD:",
                            attrs(
                                field
                            ),
                            "| text:",
                            safe_text(
                                field
                            )[:500],
                        )
                    except Exception:
                        continue

            print()
            print("--- RELEVANT NETWORK AFTER ACTION ---")

            network_tokens = (
                "offer",
                "quote",
                "lead",
                "form",
                "contact",
                "request",
                "proposal",
                "leasing",
                "rent",
                "payment",
                "finance",
                "ajax",
                "api",
            )

            for req in requests:
                low = req[
                    "url"
                ].casefold()

                if not any(
                    token in low
                    for token in network_tokens
                ):
                    continue

                print(
                    json.dumps(
                        req,
                        ensure_ascii=False,
                    )[:5000]
                )

            print()
            print("--- RESPONSE URLS AFTER ACTION ---")

            for resp in responses:
                low = resp[
                    "url"
                ].casefold()

                if not any(
                    token in low
                    for token in network_tokens
                ):
                    continue

                print(
                    json.dumps(
                        resp,
                        ensure_ascii=False,
                    )
                )

            print()
            print("=" * 100)
            print(
                "DIAGNOSTIC COMPLETE - NO FORM WAS SUBMITTED, "
                "NO PERSONAL DATA WAS ENTERED, AND NO DOWN-PAYMENT "
                "CONDITION WAS INFERRED FROM ABSENCE."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
