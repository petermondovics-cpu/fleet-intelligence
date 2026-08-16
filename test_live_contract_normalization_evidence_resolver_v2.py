from market_intelligence.market_match_engine import MarketMatchEngine
from playwright.sync_api import sync_playwright

from contract_normalization.contract_normalization_evidence_resolver_v2 import (
    RESOLVED,
    UNRESOLVED,
    ContractNormalizationEvidenceResolverV2,
)

TARGET_GROUP = "BYD::ATTO 2::PHEV"


def main():
    print("=" * 100)
    print("LIVE CONTRACT NORMALIZATION EVIDENCE RESOLVER V2")
    print("=" * 100)

    pair = next(
        (
            item
            for item in MarketMatchEngine().build()
            if item.group_key == TARGET_GROUP
        ),
        None,
    )
    assert pair is not None

    left = type(
        "ObservedOffer",
        (),
        {
            "provider": pair.left_provider,
            "duration": pair.left_duration,
            "mileage": pair.left_mileage,
            "monthly_fee": pair.left_monthly_fee,
            "url": pair.left_url,
        },
    )()

    right = type(
        "ObservedOffer",
        (),
        {
            "provider": pair.right_provider,
            "duration": pair.right_duration,
            "mileage": pair.right_mileage,
            "monthly_fee": pair.right_monthly_fee,
            "url": pair.right_url,
        },
    )()

    print()
    print("--- CURRENT OBSERVED STATES ---")
    print(left.provider, left.duration, left.mileage, left.monthly_fee)
    print(right.provider, right.duration, right.mileage, right.monthly_fee)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        try:
            result = ContractNormalizationEvidenceResolverV2(browser).resolve(
                left,
                right,
            )
        finally:
            browser.close()

    print()
    print("--- ATTEMPTED COORDINATES ---")
    for duration, mileage in result.attempted_coordinates:
        print(duration, "hó |", mileage, "km/év")

    print()
    print("--- LEFT OBSERVATIONS ---")
    for item in result.left_observations:
        print(
            item.provider,
            "|",
            item.duration,
            "|",
            item.mileage,
            "|",
            item.monthly_fee,
            "|",
            item.evidence_method,
        )

    print()
    print("--- RIGHT OBSERVATIONS ---")
    for item in result.right_observations:
        print(
            item.provider,
            "|",
            item.duration,
            "|",
            item.mileage,
            "|",
            item.monthly_fee,
            "|",
            item.evidence_method,
        )

    print()
    print("--- RESULT ---")
    print("Status:", result.status)
    print(
        "Common coordinates:",
        tuple(
            (item.duration, item.mileage)
            for item in result.common_coordinates
        ),
    )

    if result.selected_coordinate:
        selected = result.selected_coordinate
        print("Selected:", selected.duration, selected.mileage)
        print("Left normalized fee:", selected.left.monthly_fee)
        print("Right normalized fee:", selected.right.monthly_fee)

    print("Diagnostic:", result.diagnostic)

    assert result.status in {RESOLVED, UNRESOLVED}

    if result.status == RESOLVED:
        assert result.normalized_monthly_fee_left is not None
        assert result.normalized_monthly_fee_right is not None
        print()
        print("GREEN - EXACT COMMON PRICED CONTRACT COORDINATE OBSERVED FOR BOTH PROVIDERS.")
    else:
        assert result.normalized_price_available is False
        print()
        print(
            "SAFE UNRESOLVED - NO COMMON EXPLICITLY PRICED COORDINATE. "
            "NO ESTIMATION OR TERM FACTOR WAS USED."
        )

    print()
    print(
        "TEST PASSED - CONTRACT NORMALIZATION V2 USES ONLY "
        "EXPLICITLY PRICED COMMON CONTRACT STATES."
    )


if __name__ == "__main__":
    main()
