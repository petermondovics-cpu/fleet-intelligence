import json
import re
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajandlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)

SIGNALS = (
    "192312",
    "60 hónap",
    "20000",
    "ajánlat kiválasztása",
    "byd atto 2",
)

URL_HINTS = (
    "api",
    "ajax",
    "graphql",
    "offer",
    "quote",
    "vehicle",
    "car",
    "leasing",
    "rental",
    "product",
    "drupal",
    "views",
)


def norm(text):
    return " ".join((text or "").split())


def same_or_arval_owned(url):
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False

    return host == "arval.hu" or host.endswith(".arval.hu")


def response_is_interesting(response):
    req = response.request
    url_low = response.url.casefold()

    if req.resource_type in ("xhr", "fetch"):
        return True

    if any(hint in url_low for hint in URL_HINTS):
        return True

    return False


def body_signals(page):
    try:
        text = page.locator("body").inner_text()
    except Exception:
        return {}

    low = text.casefold()
    return {
        signal: signal.casefold() in low
        for signal in SIGNALS
    }


def print_signal_state(page, label):
    print()
    print(f"--- {label} ---")
    print("URL:", page.url)

    try:
        print("TITLE:", page.title())
    except Exception:
        pass

    state = body_signals(page)

    for key, value in state.items():
        print(f"{key!r}: {value}")

    try:
        body = page.locator("body").inner_text()
        low = body.casefold()

        for signal in SIGNALS:
            pos = low.find(signal.casefold())
            if pos < 0:
                continue

            print()
            print("SIGNAL CONTEXT:", signal)
            print(norm(body[max(0, pos - 300):pos + 1000]))
    except Exception:
        pass


def main():
    print("=" * 100)
    print("ARVAL EXACT-OFFER DYNAMIC LOAD / NETWORK DIAGNOSTIC V1")
    print("=" * 100)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        try:
            context = browser.new_context()

            request_rows = []
            response_rows = []
            console_rows = []
            page_errors = []

            page = context.new_page()

            def on_request(req):
                if req.resource_type not in ("xhr", "fetch") and not any(
                    hint in req.url.casefold()
                    for hint in URL_HINTS
                ):
                    return

                request_rows.append(
                    {
                        "method": req.method,
                        "resource_type": req.resource_type,
                        "url": req.url,
                        "post_data": req.post_data if req.method != "GET" else None,
                    }
                )

            def on_response(resp):
                if not response_is_interesting(resp):
                    return

                row = {
                    "status": resp.status,
                    "resource_type": resp.request.resource_type,
                    "url": resp.url,
                    "content_type": resp.headers.get("content-type"),
                    "arval_owned": same_or_arval_owned(resp.url),
                    "signals": [],
                    "preview": None,
                    "body_error": None,
                }

                ctype = (row["content_type"] or "").casefold()

                if (
                    "json" in ctype
                    or "text" in ctype
                    or "html" in ctype
                    or resp.request.resource_type in ("xhr", "fetch")
                ):
                    try:
                        text = resp.text()
                        low = text.casefold()

                        row["signals"] = [
                            signal
                            for signal in SIGNALS
                            if signal.casefold() in low
                        ]

                        if row["signals"]:
                            first = min(
                                low.find(signal.casefold())
                                for signal in row["signals"]
                                if low.find(signal.casefold()) >= 0
                            )
                            row["preview"] = norm(
                                text[max(0, first - 500):first + 2500]
                            )
                        elif same_or_arval_owned(resp.url):
                            row["preview"] = norm(text[:1500])

                    except Exception as exc:
                        row["body_error"] = repr(exc)

                response_rows.append(row)

            page.on("request", on_request)
            page.on("response", on_response)
            page.on(
                "console",
                lambda msg: console_rows.append(
                    {
                        "type": msg.type,
                        "text": msg.text,
                    }
                ),
            )
            page.on(
                "pageerror",
                lambda exc: page_errors.append(str(exc)),
            )

            page.goto(
                ARVAL_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            print_signal_state(
                page,
                "DOMCONTENTLOADED",
            )

            checkpoints = (1000, 3000, 7000, 12000)

            elapsed = 0

            for checkpoint in checkpoints:
                page.wait_for_timeout(checkpoint - elapsed)
                elapsed = checkpoint

                print_signal_state(
                    page,
                    f"AFTER {checkpoint} MS",
                )

            print()
            print("=" * 100)
            print("INTERESTING REQUESTS")
            print("=" * 100)

            if not request_rows:
                print("No interesting request captured.")

            for idx, row in enumerate(request_rows, start=1):
                print()
                print(f"REQUEST {idx}")
                print(json.dumps(row, ensure_ascii=False)[:8000])

            print()
            print("=" * 100)
            print("INTERESTING RESPONSES")
            print("=" * 100)

            if not response_rows:
                print("No interesting response captured.")

            signal_responses = [
                row for row in response_rows
                if row["signals"]
            ]

            print("Responses with target signals:", len(signal_responses))

            for idx, row in enumerate(response_rows, start=1):
                print()
                print(f"RESPONSE {idx}")
                print("status:", row["status"])
                print("resource_type:", row["resource_type"])
                print("arval_owned:", row["arval_owned"])
                print("content_type:", row["content_type"])
                print("url:", row["url"])
                print("signals:", tuple(row["signals"]))

                if row["preview"]:
                    print("preview:", row["preview"][:5000])

                if row["body_error"]:
                    print("body_error:", row["body_error"])

            print()
            print("=" * 100)
            print("CONSOLE / PAGE ERRORS")
            print("=" * 100)

            if page_errors:
                print("--- PAGE ERRORS ---")
                for item in page_errors:
                    print(item)
            else:
                print("No page errors captured.")

            important_console = [
                row for row in console_rows
                if row["type"] in ("error", "warning")
            ]

            if important_console:
                print()
                print("--- CONSOLE WARNINGS / ERRORS ---")
                for row in important_console[:100]:
                    print(json.dumps(row, ensure_ascii=False)[:5000])
            else:
                print("No console warnings/errors captured.")

            print()
            print("=" * 100)
            print("SUMMARY")
            print("=" * 100)

            final_state = body_signals(page)

            print(
                "Exact offer price visible:",
                final_state.get("192312", False),
            )
            print(
                "60-month coordinate visible:",
                final_state.get("60 hónap", False),
            )
            print(
                "20000 mileage visible:",
                final_state.get("20000", False),
            )
            print(
                "Offer CTA visible:",
                final_state.get("ajánlat kiválasztása", False),
            )
            print(
                "Network responses containing target signals:",
                len(signal_responses),
            )

            if signal_responses:
                print()
                print(
                    "GREEN DIAGNOSTIC PATH - one or more captured responses "
                    "contain exact-offer signals. Inspect those response URLs/payload previews "
                    "before writing any production resolver."
                )
            elif any(final_state.values()):
                print()
                print(
                    "DOM-ONLY / SSR PATH - exact-offer signals reached the DOM, but were not "
                    "found in captured XHR/fetch-like responses."
                )
            else:
                print()
                print(
                    "LOAD FAILURE / ALTERNATE DELIVERY PATH - exact-offer signals did not "
                    "reach the DOM and were not found in captured relevant responses. "
                    "Inspect console errors, request statuses, redirects and provider delivery behavior."
                )

            print()
            print(
                "DIAGNOSTIC COMPLETE - NO CTA WAS CLICKED, NO FORM WAS SUBMITTED, "
                "AND NO FINANCIAL CONDITION WAS INFERRED."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
