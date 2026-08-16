import json
from playwright.sync_api import sync_playwright

AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)

API_URL = (
    "https://autotartosberlet.ayvens.com/"
    "api/cars/byd/atto-2-dm-i"
)

SEARCH_KEYS = (
    "equipment",
    "equipments",
    "standard",
    "standard_equipment",
    "extras",
    "extra",
    "options",
    "optional",
    "features",
    "configuration",
    "specification",
    "specifications",
    "accessories",
    "included",
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
        if loc.count() == 0:
            continue
        try:
            loc.first.click(timeout=1500)
            page.wait_for_timeout(200)
            return
        except Exception:
            pass


def walk(node, path="$"):
    hits = []

    if isinstance(node, dict):
        for key, value in node.items():
            child_path = f"{path}.{key}"
            key_cf = str(key).casefold()

            if any(token in key_cf for token in SEARCH_KEYS):
                hits.append(
                    {
                        "path": child_path,
                        "value": value,
                    }
                )

            hits.extend(walk(value, child_path))

    elif isinstance(node, list):
        for idx, value in enumerate(node):
            hits.extend(
                walk(
                    value,
                    f"{path}[{idx}]",
                )
            )

    return hits


def summarize_value(value, max_chars=3000):
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
        )
    except TypeError:
        text = repr(value)

    if len(text) > max_chars:
        return text[:max_chars] + "\n... [TRUNCATED]"

    return text


def collect_lists(node, path="$"):
    out = []

    if isinstance(node, dict):
        for key, value in node.items():
            child_path = f"{path}.{key}"

            if isinstance(value, list) and value:
                if all(
                    isinstance(item, (str, dict))
                    for item in value
                ):
                    out.append(
                        (
                            child_path,
                            value,
                        )
                    )

            out.extend(
                collect_lists(
                    value,
                    child_path,
                )
            )

    elif isinstance(node, list):
        for idx, value in enumerate(node):
            out.extend(
                collect_lists(
                    value,
                    f"{path}[{idx}]",
                )
            )

    return out


def main():
    print("=" * 100)
    print("AYVENS EXACT-OFFER API DIAGNOSTIC V1")
    print("=" * 100)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        try:
            page = browser.new_page()

            page.goto(
                AYVENS_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            page.wait_for_timeout(1500)
            dismiss(page)

            print()
            print("--- DIRECT API FETCH ---")

            response = page.request.get(
                API_URL,
                timeout=60000,
            )

            print(
                "Status:",
                response.status,
            )

            print(
                "Content-Type:",
                response.headers.get("content-type"),
            )

            if not response.ok:
                print("API request failed.")
                print(response.text()[:5000])
                return

            data = response.json()

            print()
            print("--- TOP-LEVEL STRUCTURE ---")

            if isinstance(data, dict):
                print(
                    "Top-level keys:",
                    tuple(data.keys()),
                )
            else:
                print(
                    "Top-level type:",
                    type(data).__name__,
                )

            print()
            print("--- IDENTITY / OFFER FIELDS ---")

            identity_keys = (
                "id",
                "slug",
                "url",
                "brand",
                "model",
                "configuration",
                "fuel_type",
                "body_type",
                "price_from",
                "price_sale",
            )

            if isinstance(data, dict):
                for key in identity_keys:
                    if key in data:
                        print(
                            key,
                            "=",
                            summarize_value(
                                data[key],
                                1200,
                            ),
                        )

            print()
            print("--- EQUIPMENT-LIKE KEY PATHS ---")

            hits = walk(data)

            print(
                "Hit count:",
                len(hits),
            )

            for idx, hit in enumerate(
                hits[:100],
                start=1,
            ):
                print()
                print(f"HIT {idx}")
                print(
                    "Path:",
                    hit["path"],
                )
                print("Value:")
                print(
                    summarize_value(
                        hit["value"]
                    )
                )

            print()
            print("--- LIKELY LIST VALUES ---")

            lists = collect_lists(data)

            for idx, (path, value) in enumerate(
                lists[:80],
                start=1,
            ):
                print()
                print(f"LIST {idx}")
                print("Path:", path)
                print("Length:", len(value))
                print(
                    summarize_value(
                        value,
                        2500,
                    )
                )

            print()
            print("--- RAW JSON PREVIEW ---")

            raw = json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            )

            print(raw[:20000])

            print()
            print("=" * 100)
            print(
                "DIAGNOSTIC COMPLETE - NO EQUIPMENT "
                "INCLUSION OR STANDARD/OPTIONAL STATUS "
                "WAS INFERRED."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
