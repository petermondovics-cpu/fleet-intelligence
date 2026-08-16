"""
ARVAL EXACT-OFFER QUOTE FLOW FINANCIAL DIAGNOSTIC V3
=====================================================

Purpose
-------
Inspect the Arval exact-offer page and any safely reachable quote-selection
UI for explicit financial-condition evidence.

V3 changes
----------
- Uses ArvalOfferRouteResolver before any financial inspection.
- Starts from the provider-published exact-offer URL.
- Never assumes that repeated final URL segments are malformed.
- Never infers down payment from absence of wording.
- Never submits a quote/request form.
- Never promotes generic provider wording to exact-offer evidence.
- Prints enough DOM/navigation evidence for the next resolver iteration.

This is a DIAGNOSTIC only. It does not mutate comparison/persistence behavior.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

from playwright.sync_api import Page, Locator, sync_playwright

from scrapers.arval.cookies import accept_cookies
from scrapers.arval.offer_route_resolver import (
    ROUTE_LIVE,
    ArvalOfferRouteResolver,
)


REQUESTED_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/"
    "byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)

TARGET_PRICE = 192312
TARGET_DURATION = 60
TARGET_MILEAGE = 20000

MAX_TEXT = 1200
MAX_ELEMENT_TEXT = 700


FINANCIAL_PATTERNS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    (
        "DOWN_PAYMENT_PERCENT",
        re.compile(
            r"\b(?:önerő|onero|kezdő\s*befizetés|kezdo\s*befizetes|"
            r"első\s*befizetés|elso\s*befizetes|kezdőrészlet|kezdotoreszlet)"
            r".{0,100}?\b\d{1,3}\s*%",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "ZERO_DOWN_PAYMENT",
        re.compile(
            r"(?:0\s*%\s*(?:önerő|onero)|"
            r"(?:önerő|onero).{0,50}?0\s*%|"
            r"(?:önerő|onero)\s*nélkül|"
            r"(?:önerő|onero)\s*nelkul|"
            r"kezdő\s*befizetés\s*nélkül|"
            r"kezdo\s*befizetes\s*nelkul)",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "DOWN_PAYMENT_AMOUNT",
        re.compile(
            r"(?:önerő|onero|kezdő\s*befizetés|kezdo\s*befizetes|"
            r"első\s*befizetés|elso\s*befizetes|kezdőrészlet|kezdotoreszlet)"
            r".{0,120}?"
            r"\b\d[\d\s.,]{2,}\s*(?:Ft|HUF)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "FINANCIAL_WORDING",
        re.compile(
            r"\b(?:önerő|onero|kezdő\s*befizetés|kezdo\s*befizetes|"
            r"első\s*befizetés|elso\s*befizetes|kezdőrészlet|kezdoreszlet|"
            r"induló\s*díj|indulo\s*dij|belépési\s*díj|belepesi\s*dij|"
            r"finanszírozás|finanszirozas)\b",
            re.IGNORECASE,
        ),
    ),
)


ACTION_TERMS = (
    "ajánlat kiválasztása",
    "ajanlat kivalasztasa",
    "ajánlatot kérek",
    "ajanlatot kerek",
    "ajánlatkérés",
    "ajanlatkeres",
    "kérem az ajánlatot",
    "kerem az ajanlatot",
    "tovább",
    "tovabb",
)


@dataclass(frozen=True)
class FinancialHit:
    code: str
    text: str
    source: str


def clean(text: Optional[str]) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def clip(text: str, limit: int = MAX_TEXT) -> str:
    text = clean(text)
    if len(text) <= limit:
        return text
    return text[:limit] + " ..."


def safe_body_text(page: Page) -> str:
    try:
        return page.locator("body").inner_text(timeout=5000)
    except Exception:
        return ""


def scan_financial_text(text: str, source: str) -> List[FinancialHit]:
    result: List[FinancialHit] = []
    normalized = clean(text)

    if not normalized:
        return result

    for code, pattern in FINANCIAL_PATTERNS:
        match = pattern.search(normalized)
        if match:
            start = max(0, match.start() - 180)
            end = min(len(normalized), match.end() + 260)
            result.append(
                FinancialHit(
                    code=code,
                    text=normalized[start:end],
                    source=source,
                )
            )

    return result


def dedupe_hits(hits: Iterable[FinancialHit]) -> List[FinancialHit]:
    result: List[FinancialHit] = []
    seen = set()

    for hit in hits:
        key = (
            hit.code,
            clean(hit.text).casefold(),
            hit.source,
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(hit)

    return result


def print_hits(title: str, hits: Sequence[FinancialHit]) -> None:
    print()
    print(f"--- {title} ---")

    if not hits:
        print("No explicit financial-condition hits.")
        return

    for index, hit in enumerate(hits, 1):
        print()
        print(f"HIT {index}")
        print("code:", hit.code)
        print("source:", hit.source)
        print("text:", clip(hit.text))


def locator_text(locator: Locator) -> str:
    try:
        return clean(locator.inner_text(timeout=2000))
    except Exception:
        try:
            return clean(locator.text_content(timeout=2000))
        except Exception:
            return ""


def describe_locator(locator: Locator) -> dict:
    try:
        return locator.evaluate(
            """el => ({
                tag: el.tagName,
                id: el.id || null,
                className: typeof el.className === 'string' ? el.className : null,
                role: el.getAttribute('role'),
                href: el.getAttribute('href'),
                type: el.getAttribute('type'),
                name: el.getAttribute('name'),
                ariaLabel: el.getAttribute('aria-label'),
                dataTestId: el.getAttribute('data-testid')
            })"""
        )
    except Exception:
        return {}


def find_action_candidates(page: Page) -> List[Tuple[Locator, str, dict]]:
    selectors = (
        "a",
        "button",
        "[role='button']",
        "input[type='button']",
        "input[type='submit']",
    )

    candidates: List[Tuple[Locator, str, dict]] = []
    seen = set()

    for selector in selectors:
        locator = page.locator(selector)

        try:
            count = min(locator.count(), 300)
        except Exception:
            continue

        for index in range(count):
            item = locator.nth(index)

            try:
                if not item.is_visible():
                    continue
            except Exception:
                continue

            text = locator_text(item)

            if not text:
                try:
                    text = clean(item.get_attribute("value"))
                except Exception:
                    text = ""

            folded = text.casefold()

            if not any(term in folded for term in ACTION_TERMS):
                continue

            attrs = describe_locator(item)
            key = (
                text.casefold(),
                attrs.get("href"),
                attrs.get("id"),
                attrs.get("className"),
            )

            if key in seen:
                continue

            seen.add(key)
            candidates.append((item, text, attrs))

    return candidates


def print_action_candidates(
    candidates: Sequence[Tuple[Locator, str, dict]]
) -> None:
    print()
    print("--- OFFER / QUOTE ACTION CANDIDATES ---")
    print("Count:", len(candidates))

    if not candidates:
        print("No safely identifiable quote-selection action found.")
        return

    for index, (_, text, attrs) in enumerate(candidates, 1):
        print()
        print(f"ACTION {index}")
        print("text:", clip(text, 300))
        print("attrs:", attrs)


def choose_safe_action(
    candidates: Sequence[Tuple[Locator, str, dict]]
) -> Optional[Tuple[Locator, str, dict]]:
    """
    Choose only an action that looks like quote selection/navigation.

    Submit-like actions are deliberately excluded. The diagnostic must not
    send a lead or quote request.
    """

    preferred_terms = (
        "ajánlat kiválasztása",
        "ajanlat kivalasztasa",
    )

    for item in candidates:
        locator, text, attrs = item
        folded = text.casefold()

        if not any(term in folded for term in preferred_terms):
            continue

        element_type = clean(attrs.get("type")).casefold()

        if element_type == "submit":
            continue

        return locator, text, attrs

    return None


def scan_visible_financial_elements(page: Page) -> List[FinancialHit]:
    selector = (
        "p, span, div, li, label, strong, small, "
        "h1, h2, h3, h4, td, th"
    )

    locator = page.locator(selector)
    hits: List[FinancialHit] = []

    try:
        count = min(locator.count(), 1000)
    except Exception:
        return hits

    for index in range(count):
        item = locator.nth(index)

        try:
            if not item.is_visible():
                continue
        except Exception:
            continue

        text = locator_text(item)

        if not text or len(text) > 2500:
            continue

        local_hits = scan_financial_text(
            text,
            source="VISIBLE_DOM_ELEMENT",
        )

        hits.extend(local_hits)

    return dedupe_hits(hits)


def print_exact_offer_state(page: Page) -> None:
    print()
    print("--- EXACT OFFER STATE ---")

    body = clean(safe_body_text(page))
    compact = body.replace(" ", "")

    print("URL:", page.url)
    print("TITLE:", page.title())
    print(
        f"Target price {TARGET_PRICE}:",
        str(TARGET_PRICE) in compact,
    )
    print(
        f"Target duration {TARGET_DURATION}:",
        bool(
            re.search(
                rf"\b{TARGET_DURATION}\s*(?:hó|hónap)\b",
                body,
                re.IGNORECASE,
            )
        ),
    )
    print(
        f"Target mileage {TARGET_MILEAGE}:",
        str(TARGET_MILEAGE) in compact,
    )


def inspect_forms(page: Page) -> None:
    print()
    print("--- FORM / INPUT DIAGNOSTIC ---")

    forms = page.locator("form")

    try:
        form_count = forms.count()
    except Exception:
        form_count = 0

    print("Forms:", form_count)

    inputs = page.locator(
        "input, select, textarea"
    )

    try:
        input_count = min(inputs.count(), 200)
    except Exception:
        input_count = 0

    interesting = []

    for index in range(input_count):
        item = inputs.nth(index)
        attrs = describe_locator(item)

        joined = " ".join(
            clean(str(value))
            for value in attrs.values()
            if value
        ).casefold()

        try:
            placeholder = clean(
                item.get_attribute("placeholder")
            )
        except Exception:
            placeholder = ""

        joined += " " + placeholder.casefold()

        if any(
            token in joined
            for token in (
                "onero",
                "önerő",
                "deposit",
                "down",
                "payment",
                "finance",
                "finansz",
                "kezd",
            )
        ):
            interesting.append(
                (
                    attrs,
                    placeholder,
                )
            )

    if not interesting:
        print("No financial-looking form controls.")
        return

    for index, (attrs, placeholder) in enumerate(interesting, 1):
        print()
        print(f"CONTROL {index}")
        print("attrs:", attrs)
        print("placeholder:", placeholder)


def main() -> None:
    print("=" * 100)
    print("ARVAL EXACT-OFFER QUOTE FLOW FINANCIAL DIAGNOSTIC V3")
    print("=" * 100)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        try:
            page = browser.new_page()

            print()
            print("--- ROUTE RESOLUTION ---")

            route = (
                ArvalOfferRouteResolver()
                .resolve(
                    page,
                    REQUESTED_URL,
                    timeout=60000,
                    settle_ms=1800,
                )
            )

            print("Status:", route.status)
            print("Requested:", route.requested_url)
            print("Candidates:", route.candidates)
            print("Resolved:", route.resolved_url)
            print("Diagnostic:", route.diagnostic)

            assert route.status == ROUTE_LIVE
            assert route.resolved_url

            try:
                accept_cookies(page)
            except Exception:
                pass

            page.wait_for_timeout(1200)

            print_exact_offer_state(page)

            before_body = safe_body_text(page)

            before_hits = dedupe_hits(
                scan_financial_text(
                    before_body,
                    source="EXACT_OFFER_BODY",
                )
                + scan_visible_financial_elements(page)
            )

            print_hits(
                "FINANCIAL EVIDENCE BEFORE ACTION",
                before_hits,
            )

            candidates = find_action_candidates(page)
            print_action_candidates(candidates)

            action = choose_safe_action(candidates)

            if action is None:
                print()
                print(
                    "No safe 'AJÁNLAT KIVÁLASZTÁSA' action was found. "
                    "No click attempted."
                )

                inspect_forms(page)

                print()
                print("=" * 100)
                print("SUMMARY")
                print("=" * 100)
                print("Route validated:", True)
                print(
                    "Explicit financial hits:",
                    len(before_hits),
                )
                print("Safe quote-flow action clicked:", False)
                print("Form submitted:", False)

                if before_hits:
                    print(
                        "RESULT: EXPLICIT FINANCIAL WORDING OBSERVED "
                        "ON THE EXACT OFFER PAGE; REVIEW HIT SCOPE "
                        "BEFORE PROMOTION."
                    )
                else:
                    print(
                        "RESULT: NO EXPLICIT DOWN-PAYMENT CONDITION "
                        "WAS OBSERVED. DOWN PAYMENT REMAINS UNKNOWN."
                    )

                print()
                print(
                    "DIAGNOSTIC COMPLETE - NO FINANCIAL CONDITION "
                    "WAS INFERRED."
                )
                return

            locator, text, attrs = action

            print()
            print("--- SAFE ACTION SELECTED ---")
            print("text:", text)
            print("attrs:", attrs)

            before_url = page.url

            try:
                locator.click(
                    timeout=8000
                )
            except Exception as exc:
                print(
                    "Safe action click failed:",
                    f"{type(exc).__name__}: {exc}",
                )

                print()
                print(
                    "DIAGNOSTIC COMPLETE - NO FORM WAS SUBMITTED "
                    "AND NO FINANCIAL CONDITION WAS INFERRED."
                )
                return

            page.wait_for_timeout(1800)

            print()
            print("--- AFTER SAFE ACTION ---")
            print("Before URL:", before_url)
            print("After URL:", page.url)

            after_body = safe_body_text(page)

            after_hits = dedupe_hits(
                scan_financial_text(
                    after_body,
                    source="POST_SELECTION_BODY",
                )
                + scan_visible_financial_elements(page)
            )

            print_hits(
                "FINANCIAL EVIDENCE AFTER ACTION",
                after_hits,
            )

            inspect_forms(page)

            all_hits = dedupe_hits(
                list(before_hits)
                + list(after_hits)
            )

            explicit_down_payment = [
                hit
                for hit in all_hits
                if hit.code
                in {
                    "DOWN_PAYMENT_PERCENT",
                    "ZERO_DOWN_PAYMENT",
                    "DOWN_PAYMENT_AMOUNT",
                }
            ]

            print()
            print("=" * 100)
            print("SUMMARY")
            print("=" * 100)
            print("Route validated:", True)
            print(
                "Exact-offer URL:",
                route.resolved_url,
            )
            print(
                "Financial wording hits:",
                len(all_hits),
            )
            print(
                "Explicit down-payment hits:",
                len(explicit_down_payment),
            )
            print("Safe quote-flow action clicked:", True)
            print("Form submitted:", False)

            if explicit_down_payment:
                print(
                    "RESULT: EXPLICIT DOWN-PAYMENT EVIDENCE "
                    "WAS OBSERVED. REVIEW THE PRINTED SOURCE TEXT "
                    "AND SCOPE BEFORE PROMOTION."
                )
            else:
                print(
                    "RESULT: NO EXPLICIT DOWN-PAYMENT PERCENTAGE, "
                    "AMOUNT, OR ZERO-DOWN STATEMENT WAS OBSERVED. "
                    "DOWN PAYMENT REMAINS UNKNOWN."
                )

            print()
            print(
                "DIAGNOSTIC COMPLETE - NO FORM WAS SUBMITTED "
                "AND NO FINANCIAL CONDITION WAS INFERRED."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
