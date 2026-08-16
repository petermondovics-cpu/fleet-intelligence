from playwright.sync_api import sync_playwright

from comparison.evidence_aware_comparable import (
    EvidenceAwareComparableOfferEngine,
)
from models.comparable_offer import (
    COMPARABLE,
    INSUFFICIENT_EVIDENCE,
    NORMALIZATION_REQUIRED,
    NOT_COMPARABLE,
)
from scrapers.arval.evidence_aware_builder import (
    ArvalEvidenceAwareBuilder,
)
from scrapers.ayvens.evidence_aware_builder import (
    AyvensEvidenceAwareBuilder,
)


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


def dismiss_cookies(
    page,
):
    selectors = [
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
    ]

    for selector in selectors:
        locator = page.locator(
            selector
        )

        if locator.count() == 0:
            continue

        try:
            locator.first.click(
                timeout=2500
            )
            page.wait_for_timeout(
                500
            )
            return
        except Exception:
            continue


def print_offer(
    label,
    wrapped,
):

    composite = wrapped.composite

    print(
        "\n---",
        label,
        "---",
    )

    print(
        "Provider:",
        composite.provider,
    )

    print(
        "Vehicle:",
        composite.offer.brand,
        composite.offer.model,
        "/",
        composite.offer.trim,
    )

    print(
        "Fuel:",
        composite.offer.fuel_type,
    )

    print(
        "Contract:",
        f"{composite.duration} months / "
        f"{composite.mileage:,} km/year",
    )

    print(
        "Monthly fee:",
        f"{composite.monthly_fee:,} Ft",
    )

    print(
        "Standard equipment:",
        composite.standard_equipment_count,
        "/ status:",
        wrapped.equipment_evidence.standard_status,
    )

    print(
        "Optional equipment:",
        composite.optional_equipment_count,
        "/ status:",
        wrapped.equipment_evidence.optional_status,
    )

    print(
        "Included services:",
        composite.included_service_count,
    )

    print(
        "Down payment known:",
        composite.down_payment_known,
    )


def main():

    print(
        "=" * 80
    )
    print(
        "LIVE ARVAL ↔ AYVENS "
        "EVIDENCE-AWARE COMPARISON V1"
    )
    print(
        "=" * 80
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        # ----------------------------------------------------
        # ARVAL
        # ----------------------------------------------------

        arval_page = (
            browser.new_page()
        )

        print(
            "\nOpening Arval..."
        )

        arval_page.goto(
            ARVAL_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        arval_page.wait_for_timeout(
            3000
        )

        dismiss_cookies(
            arval_page
        )

        arval = (
            ArvalEvidenceAwareBuilder()
            .build(
                arval_page
            )
        )

        # ----------------------------------------------------
        # AYVENS
        # ----------------------------------------------------

        ayvens_page = (
            browser.new_page()
        )

        print(
            "Opening Ayvens..."
        )

        ayvens_page.goto(
            AYVENS_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        ayvens_page.wait_for_timeout(
            3000
        )

        dismiss_cookies(
            ayvens_page
        )

        ayvens = (
            AyvensEvidenceAwareBuilder()
            .build(
                ayvens_page
            )
        )

        print_offer(
            "ARVAL",
            arval,
        )

        print_offer(
            "AYVENS",
            ayvens,
        )

        # ----------------------------------------------------
        # PROVIDER EVIDENCE ASSERTIONS
        # ----------------------------------------------------

        assert (
            arval.equipment_evidence
            .standard_status
            == "NOT_PUBLISHED"
        )

        assert (
            arval.equipment_evidence
            .optional_status
            == "NOT_PUBLISHED"
        )

        assert (
            ayvens.equipment_evidence
            .standard_status
            in {
                "PUBLISHED",
                "NOT_PUBLISHED",
                "PARSING_UNRESOLVED",
            }
        )

        assert (
            ayvens.equipment_evidence
            .optional_status
            in {
                "PUBLISHED",
                "NOT_PUBLISHED",
                "PARSING_UNRESOLVED",
            }
        )

        print(
            "\nTEST 1 PASSED - "
            "PROVIDER EQUIPMENT EVIDENCE "
            "ATTACHED"
        )

        # ----------------------------------------------------
        # EVIDENCE-AWARE COMPARISON
        # ----------------------------------------------------

        engine = (
            EvidenceAwareComparableOfferEngine()
        )

        result = engine.compare(
            arval,
            ayvens,
        )

        print(
            "\n--- COMPARISON RESULT ---"
        )

        print(
            "Status:",
            result.status,
        )

        for reason in (
            result.reasons
        ):
            print(
                "-",
                reason.code,
                ":",
                reason.message,
            )

        assert result.status in {
            COMPARABLE,
            NORMALIZATION_REQUIRED,
            NOT_COMPARABLE,
            INSUFFICIENT_EVIDENCE,
        }

        # This test's safety requirement:
        # Arval's non-published equipment must never be interpreted
        # as an observed zero-equipment specification.
        if (
            result.status
            != NOT_COMPARABLE
        ):
            assert (
                result.status
                == INSUFFICIENT_EVIDENCE
            )

            assert any(
                reason.code
                == "EQUIPMENT_EVIDENCE_INCOMPLETE"
                for reason in result.reasons
            )

        print(
            "TEST 2 PASSED - "
            "NO FALSE EQUIPMENT COMPARISON"
        )

        # ----------------------------------------------------
        # NO PRICE WINNER AT THIS LAYER
        # ----------------------------------------------------

        assert not hasattr(
            result,
            "price_winner",
        )

        print(
            "TEST 3 PASSED - "
            "COMPARABILITY LAYER DOES NOT "
            "DECLARE A PRICE WINNER"
        )

        print(
            "\nIMPORTANT:"
        )

        print(
            "If the live vehicles themselves differ, "
            "NOT_COMPARABLE is correct."
        )

        print(
            "If vehicle/contract identity is otherwise "
            "comparable, Arval NOT_PUBLISHED equipment "
            "must force INSUFFICIENT_EVIDENCE."
        )

        print(
            "\n"
            + "=" * 80
        )

        print(
            "LIVE ARVAL ↔ AYVENS "
            "EVIDENCE-AWARE V1 COMPLETED"
        )

        print(
            "=" * 80
        )

        browser.close()


if __name__ == "__main__":
    main()
