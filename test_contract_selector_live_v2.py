from playwright.sync_api import sync_playwright

from scrapers.arval.scraper import ArvalScraper
from scrapers.ayvens.scraper import AyvensScraper
from models.contract_variant import DEFAULT_CONTRACT_VARIANTS


ARVAL_TEST_URL = (
    "https://www.arval.hu/"
    "kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/"
    "byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)

AYVENS_TEST_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)


def dismiss_cookie_overlay(page, provider):
    """
    Close the OneTrust overlay if it is present.

    This is deliberately best-effort. If no banner exists,
    the page is left untouched.
    """

    candidates = [
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
        "button:has-text('Összes elutasítása')",
    ]

    for selector in candidates:
        locator = page.locator(selector)

        if locator.count() == 0:
            continue

        try:
            locator.first.click(
                timeout=3000
            )
            page.wait_for_timeout(500)
            print(
                f"Cookie overlay handled "
                f"({provider})"
            )
            return
        except Exception:
            continue

    # If the consent SDK is still visible, try its
    # visible buttons by role/text.
    sdk = page.locator(
        "#onetrust-consent-sdk"
    )

    if sdk.count() > 0:
        try:
            if sdk.first.is_visible():

                buttons = sdk.locator(
                    "button"
                )

                for i in range(
                    buttons.count()
                ):

                    button = buttons.nth(i)

                    try:
                        if button.is_visible():
                            button.click(
                                timeout=2000
                            )
                            page.wait_for_timeout(
                                500
                            )
                            print(
                                f"Cookie overlay handled "
                                f"({provider})"
                            )
                            return
                    except Exception:
                        continue
        except Exception:
            pass

    print(
        f"No active cookie overlay found "
        f"({provider})"
    )


def visible_texts(page, selectors):
    result = []

    for selector in selectors:
        locators = page.locator(selector)

        for i in range(locators.count()):
            item = locators.nth(i)

            try:
                if not item.is_visible():
                    continue

                text = (
                    item.inner_text()
                    .strip()
                )

                if text:
                    result.append(
                        (
                            selector,
                            text,
                        )
                    )
            except Exception:
                continue

    return result


def find_arval_contract_control(
    page,
    label,
):
    """
    Return the interactive element associated with an
    Arval configuration label.

    We deliberately inspect the DOM around the label
    instead of using a global text search.
    """

    block = (
        page.locator(
            "p.OfferConfigurationTitle"
        )
        .filter(
            has_text=label
        )
        .first
    )

    if block.count() == 0:
        raise ValueError(
            f"Arval label not found: {label}"
        )

    parent = block.locator(
        "xpath=.."
    )

    return parent


def select_arval_value(
    page,
    label,
    candidates,
):
    parent = find_arval_contract_control(
        page,
        label,
    )

    # Native select.
    select = parent.locator(
        "select"
    )

    if select.count() > 0:

        options = select.locator(
            "option"
        )

        for i in range(
            options.count()
        ):

            option = options.nth(i)

            text = (
                option.inner_text()
                .strip()
            )

            value = (
                option.get_attribute(
                    "value"
                )
            )

            if matches_value(
                text,
                value,
                candidates,
            ):

                if value is not None:
                    select.select_option(
                        value=value
                    )
                else:
                    select.select_option(
                        label=text
                    )

                return

    # Buttons / controls inside the same
    # configuration block.
    controls = parent.locator(
        "button, label, "
        "[role='option'], "
        "[role='radio'], "
        "[role='button']"
    )

    for i in range(
        controls.count()
    ):

        control = controls.nth(i)

        try:
            text = (
                control.inner_text()
                .strip()
            )
        except Exception:
            continue

        if matches_value(
            text,
            None,
            candidates,
        ):

            control.click(
                timeout=5000
            )
            return

    # Some Arval controls may use spans/divs
    # as clickable values. Still keep the search
    # scoped to the configuration parent.
    for candidate in candidates:

        locator = parent.get_by_text(
            candidate,
            exact=True,
        )

        if locator.count() > 0:

            locator.first.click(
                timeout=5000
            )
            return

    raise ValueError(
        f"Arval value not found "
        f"for {label}: {candidates}"
    )


def select_arval_contract(
    page,
    variant,
):
    select_arval_value(
        page,
        "Időtartam",
        [
            f"{variant.duration} hónap",
            f"{variant.duration} hó",
            str(variant.duration),
        ],
    )

    page.wait_for_timeout(500)

    select_arval_value(
        page,
        "Futásteljesítmény",
        [
            f"{variant.mileage:,} km/év".replace(
                ",", " "
            ),
            f"{variant.mileage:,} km/év",
            f"{variant.mileage} km/év",
            str(variant.mileage),
        ],
    )


def select_ayvens_duration(
    page,
    duration,
):
    """
    Ayvens duration selector.

    The live page exposes the current configuration as
    a paragraph such as:
        48 hónap, 20.000 km/év

    Therefore we search for the configuration control
    rather than global text like "60", which can match
    unrelated values such as 160KW.
    """

    exact_candidates = [
        f"{duration} hónap,",
        f"{duration} hónap",
    ]

    # First look for elements containing the complete
    # contract text pattern.
    paragraphs = page.locator(
        "p.font-size-16px.font-source"
    )

    for i in range(
        paragraphs.count()
    ):

        item = paragraphs.nth(i)

        try:
            if not item.is_visible():
                continue

            text = (
                item.inner_text()
                .strip()
            )
        except Exception:
            continue

        if not any(
            candidate in text
            for candidate in exact_candidates
        ):
            continue

        # Only accept text that actually looks like
        # the contract summary.
        if "km/év" not in text:
            continue

        # Click the exact contract-summary element.
        item.click(
            timeout=5000
        )
        return

    raise ValueError(
        f"Ayvens duration control not found "
        f"for {duration} months"
    )


def select_ayvens_mileage(
    page,
    mileage,
):
    """
    After duration selection, locate a mileage value
    only inside an actual contract-like text/control.

    Avoid global numeric searches.
    """

    normalized = str(
        mileage
    )

    candidates = {
        normalized,
        f"{mileage:,}".replace(
            ",", "."
        ),
        f"{mileage:,}".replace(
            ",", " "
        ),
    }

    # Inspect common clickable controls first.
    controls = page.locator(
        "button, label, "
        "[role='option'], "
        "[role='radio'], "
        "[role='button']"
    )

    for i in range(
        controls.count()
    ):

        item = controls.nth(i)

        try:
            if not item.is_visible():
                continue

            text = (
                item.inner_text()
                .strip()
            )
        except Exception:
            continue

        if (
            "km" not in text.lower()
            and "év" not in text.lower()
        ):
            continue

        if any(
            candidate in normalize_text(text)
            for candidate in candidates
        ):

            item.click(
                timeout=5000
            )
            return

    # Then inspect text elements that contain both
    # the mileage and the contract unit.
    text_elements = page.locator(
        "p, span, div"
    )

    for i in range(
        text_elements.count()
    ):

        item = text_elements.nth(i)

        try:
            if not item.is_visible():
                continue

            text = (
                item.inner_text()
                .strip()
            )
        except Exception:
            continue

        if "km/év" not in text:
            continue

        if any(
            candidate in normalize_text(text)
            for candidate in candidates
        ):

            try:
                item.click(
                    timeout=3000
                )
                return
            except Exception:
                continue

    raise ValueError(
        f"Ayvens mileage control not found "
        f"for {mileage} km/year"
    )


def select_ayvens_contract(
    page,
    variant,
):
    select_ayvens_duration(
        page,
        variant.duration,
    )

    page.wait_for_timeout(700)

    select_ayvens_mileage(
        page,
        variant.mileage,
    )


def matches_value(
    text,
    value,
    candidates,
):
    haystacks = [
        text or "",
        value or "",
    ]

    for haystack in haystacks:

        normalized = normalize_text(
            haystack
        )

        for candidate in candidates:

            expected = normalize_text(
                candidate
            )

            if (
                expected
                and expected == normalized
            ):
                return True

    return False


def normalize_text(text):
    return (
        str(text)
        .strip()
        .lower()
        .replace(".", "")
        .replace(",", "")
        .replace(" ", "")
        .replace("/", "")
    )


def verify_contract(
    page,
    provider,
    variant,
):
    if provider == "Arval":

        from scrapers.arval.parser import (
            ArvalParser,
        )

        parser = ArvalParser()

    else:

        from scrapers.ayvens.parser import (
            AyvensParser,
        )

        parser = AyvensParser()

    duration = (
        parser.parse_duration(
            page
        )
    )

    mileage = (
        parser.parse_mileage(
            page
        )
    )

    monthly_fee = (
        parser.parse_monthly_fee(
            page
        )
    )

    return (
        duration,
        mileage,
        monthly_fee,
    )


def run_provider_test(
    provider,
    scraper,
    url,
):
    print(
        "\n"
        + "=" * 72
    )

    print(
        f"{provider} CONTRACT SELECTOR LIVE TEST V2"
    )

    print(
        "=" * 72
    )

    passed = 0
    rejected = 0

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        for variant in DEFAULT_CONTRACT_VARIANTS:

            print(
                "\n"
                + "-" * 72
            )

            print(
                f"REQUESTED: "
                f"{variant.duration} hó / "
                f"{variant.mileage:,} km"
            )

            try:

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

                page.wait_for_timeout(
                    1500
                )

                dismiss_cookie_overlay(
                    page,
                    provider,
                )

                if provider == "Arval":

                    # Arval already has its own
                    # cookie handler; run it as well
                    # after navigation.
                    try:
                        from scrapers.arval.cookies import (
                            accept_cookies,
                        )

                        accept_cookies(page)
                    except Exception:
                        pass

                    dismiss_cookie_overlay(
                        page,
                        provider,
                    )

                    select_arval_contract(
                        page,
                        variant,
                    )

                else:

                    dismiss_cookie_overlay(
                        page,
                        provider,
                    )

                    select_ayvens_contract(
                        page,
                        variant,
                    )

                page.wait_for_timeout(
                    1000
                )

                observed_duration, observed_mileage, monthly_fee = (
                    verify_contract(
                        page,
                        provider,
                        variant,
                    )
                )

                print(
                    f"OBSERVED: "
                    f"{observed_duration} hó / "
                    f"{observed_mileage:,} km"
                )

                print(
                    f"PRICE: "
                    f"{monthly_fee:,} Ft"
                )

                if (
                    observed_duration
                    != variant.duration
                    or observed_mileage
                    != variant.mileage
                ):

                    print(
                        "STATUS: REJECTED"
                    )

                    print(
                        "Reason: page did not "
                        "confirm requested contract."
                    )

                    rejected += 1
                    continue

                if monthly_fee <= 0:
                    raise ValueError(
                        "Monthly fee is not positive."
                    )

                print(
                    "STATUS: PASS"
                )

                passed += 1

            except Exception as exc:

                print(
                    "STATUS: REJECTED"
                )

                print(
                    f"Reason: {exc}"
                )

                rejected += 1

        browser.close()

    print(
        "\n"
        + "=" * 72
    )

    print(
        f"{provider} SUMMARY"
    )

    print(
        "=" * 72
    )

    print(
        f"Passed:   {passed}"
    )

    print(
        f"Rejected: {rejected}"
    )

    return passed, rejected


def main():

    print(
        "\n"
        + "=" * 72
    )

    print(
        "FLEETIQ CONTRACT SELECTOR LIVE TEST V2"
    )

    print(
        "=" * 72
    )

    arval_passed, arval_rejected = (
        run_provider_test(
            "Arval",
            ArvalScraper(),
            ARVAL_TEST_URL,
        )
    )

    ayvens_passed, ayvens_rejected = (
        run_provider_test(
            "Ayvens",
            AyvensScraper(),
            AYVENS_TEST_URL,
        )
    )

    total_passed = (
        arval_passed
        + ayvens_passed
    )

    total_rejected = (
        arval_rejected
        + ayvens_rejected
    )

    print(
        "\n"
        + "=" * 72
    )

    print(
        "FINAL RESULT V2"
    )

    print(
        "=" * 72
    )

    print(
        f"Passed:   {total_passed}"
    )

    print(
        f"Rejected: {total_rejected}"
    )

    print(
        f"Total:    "
        f"{total_passed + total_rejected}"
    )

    print(
        "\nA REJECTED VARIANT IS SAFE:"
    )

    print(
        "The test never creates an Offer unless "
        "the page parser confirms the requested "
        "duration and mileage."
    )


if __name__ == "__main__":
    main()
