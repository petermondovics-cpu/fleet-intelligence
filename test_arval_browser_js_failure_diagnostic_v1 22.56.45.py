import json
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


def norm(text):
    return " ".join((text or "").split())


def is_arval(url):
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return host == "arval.hu" or host.endswith(".arval.hu")


def main():
    print("=" * 108)
    print("ARVAL BROWSER ENVIRONMENT / JS FAILURE DIAGNOSTIC V1")
    print("=" * 108)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        try:
            context = browser.new_context()
            page = context.new_page()

            requests_failed = []
            responses = []
            console = []
            page_errors = []

            page.on(
                "requestfailed",
                lambda req: requests_failed.append(
                    {
                        "url": req.url,
                        "resource_type": req.resource_type,
                        "failure": req.failure,
                    }
                ),
            )

            def on_response(resp):
                req = resp.request
                if (
                    req.resource_type in ("document", "script", "xhr", "fetch")
                    or resp.status >= 400
                    or is_arval(resp.url)
                ):
                    responses.append(
                        {
                            "status": resp.status,
                            "resource_type": req.resource_type,
                            "url": resp.url,
                            "content_type": resp.headers.get("content-type"),
                        }
                    )

            page.on("response", on_response)

            page.on(
                "console",
                lambda msg: console.append(
                    {
                        "type": msg.type,
                        "text": msg.text,
                        "location": msg.location,
                    }
                ),
            )

            def on_page_error(exc):
                page_errors.append(
                    {
                        "message": str(exc),
                        "name": getattr(exc, "name", None),
                        "stack": getattr(exc, "stack", None),
                    }
                )

            page.on("pageerror", on_page_error)

            main_response = page.goto(
                ARVAL_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            page.wait_for_timeout(12000)

            print()
            print("--- MAIN DOCUMENT ---")
            print("Final URL:", page.url)

            if main_response is not None:
                print("HTTP:", main_response.status)
                print("Content-Type:", main_response.headers.get("content-type"))
            else:
                print("Main response unavailable.")

            try:
                print("Title:", page.title())
            except Exception as exc:
                print("Title error:", repr(exc))

            print()
            print("--- BROWSER / JS CAPABILITIES ---")

            capabilities = page.evaluate(
                """
                () => ({
                    userAgent: navigator.userAgent,
                    platform: navigator.platform,
                    language: navigator.language,
                    languages: navigator.languages,
                    webdriver: navigator.webdriver,
                    stringIncludesType: typeof String.prototype.includes,
                    arrayIncludesType: typeof Array.prototype.includes,
                    objectIncludesType: typeof Object.prototype.includes,
                    promiseType: typeof Promise,
                    fetchType: typeof fetch,
                    urlType: typeof URL,
                    intersectionObserverType: typeof IntersectionObserver,
                    intlType: typeof Intl,
                    readyState: document.readyState,
                    htmlLang: document.documentElement.lang,
                })
                """
            )

            print(json.dumps(capabilities, ensure_ascii=False, indent=2))

            print()
            print("--- EXACT OFFER SIGNALS IN DOM ---")

            body = page.locator("body").inner_text()
            low = body.casefold()

            for signal in SIGNALS:
                present = signal.casefold() in low
                print(f"{signal!r}: {present}")

                if present:
                    pos = low.find(signal.casefold())
                    print(
                        "  context:",
                        norm(body[max(0, pos - 250):pos + 900]),
                    )

            print()
            print("--- DRUPAL / BOOTSTRAP STATE ---")

            bootstrap = page.evaluate(
                """
                () => {
                    const safe = (fn) => {
                        try { return fn(); }
                        catch (e) { return {error: String(e)}; }
                    };

                    return {
                        drupalType: typeof window.Drupal,
                        drupalSettingsType: typeof window.drupalSettings,
                        jqueryType: typeof window.jQuery,
                        onceType: typeof window.once,
                        drupalKeys: safe(() =>
                            window.Drupal ? Object.keys(window.Drupal).slice(0, 100) : []
                        ),
                        drupalSettingsKeys: safe(() =>
                            window.drupalSettings
                                ? Object.keys(window.drupalSettings).slice(0, 100)
                                : []
                        ),
                        bodyClasses: document.body ? document.body.className : null,
                    };
                }
                """
            )

            print(json.dumps(bootstrap, ensure_ascii=False, indent=2))

            print()
            print("--- SCRIPT INVENTORY FROM DOM ---")

            scripts = page.evaluate(
                """
                () => Array.from(document.scripts).map((s, i) => ({
                    index: i,
                    src: s.src || null,
                    type: s.type || null,
                    async: !!s.async,
                    defer: !!s.defer,
                    integrity: s.integrity || null,
                    crossOrigin: s.crossOrigin || null,
                    inlineLength: s.src ? 0 : (s.textContent || '').length,
                    inlinePreview: s.src
                        ? null
                        : (s.textContent || '').trim().slice(0, 700),
                }))
                """
            )

            for item in scripts:
                print(json.dumps(item, ensure_ascii=False)[:4000])

            print()
            print("--- SCRIPT / DOCUMENT / XHR / FETCH RESPONSES ---")

            for idx, row in enumerate(responses, start=1):
                print(
                    f"{idx:03d} | {row['status']} | "
                    f"{row['resource_type']} | "
                    f"{row['content_type']} | {row['url']}"
                )

            print()
            print("--- HTTP >= 400 ---")

            bad = [row for row in responses if row["status"] >= 400]

            if not bad:
                print("No captured HTTP >= 400 responses.")
            else:
                for row in bad:
                    print(json.dumps(row, ensure_ascii=False))

            print()
            print("--- REQUEST FAILURES ---")

            if not requests_failed:
                print("No requestfailed events captured.")
            else:
                for row in requests_failed:
                    print(json.dumps(row, ensure_ascii=False)[:5000])

            print()
            print("--- PAGE ERRORS WITH STACK ---")

            if not page_errors:
                print("No page errors captured.")
            else:
                for idx, row in enumerate(page_errors, start=1):
                    print()
                    print(f"PAGE ERROR {idx}")
                    print("message:", row["message"])
                    print("name:", row["name"])
                    print("stack:", row["stack"])

            print()
            print("--- CONSOLE ERRORS / WARNINGS ---")

            important = [
                row for row in console
                if row["type"] in ("error", "warning")
            ]

            if not important:
                print("No console errors/warnings captured.")
            else:
                for idx, row in enumerate(important, start=1):
                    print()
                    print(f"CONSOLE {idx}")
                    print(json.dumps(row, ensure_ascii=False, indent=2)[:8000])

            print()
            print("--- POLYFILL REFERENCES ---")

            polyfill_refs = page.evaluate(
                """
                () => {
                    const html = document.documentElement.outerHTML;
                    const matches = html.match(
                        /[^"'\\s<>]*polyfill[^"'\\s<>]*/gi
                    ) || [];
                    return Array.from(new Set(matches)).slice(0, 100);
                }
                """
            )

            if not polyfill_refs:
                print("No polyfill references found in current DOM HTML.")
            else:
                for ref in polyfill_refs:
                    print(ref)

            print()
            print("=" * 108)
            print("SUMMARY")
            print("=" * 108)

            print("Main HTTP:", main_response.status if main_response else None)
            print("Captured scripts:", sum(1 for r in responses if r["resource_type"] == "script"))
            print("HTTP >=400:", len(bad))
            print("Request failures:", len(requests_failed))
            print("Page errors:", len(page_errors))
            print("Console errors/warnings:", len(important))
            print("String.includes:", capabilities["stringIncludesType"])
            print("Array.includes:", capabilities["arrayIncludesType"])
            print("Object.includes:", capabilities["objectIncludesType"])
            print("Drupal:", bootstrap["drupalType"])
            print("drupalSettings:", bootstrap["drupalSettingsType"])

            print()
            print(
                "DIAGNOSTIC COMPLETE - NO POLYFILL WAS INJECTED, NO RESOURCE WAS MODIFIED, "
                "NO CTA WAS CLICKED, AND NO PROVIDER STATE WAS FABRICATED."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
