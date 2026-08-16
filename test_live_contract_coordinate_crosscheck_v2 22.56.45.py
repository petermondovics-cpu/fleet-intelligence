from market_intelligence.market_match_engine import MarketMatchEngine
from playwright.sync_api import sync_playwright

from contract_normalization.arval_contract_variant_observer import (
    ArvalContractVariantObserver,
)
from contract_normalization.ayvens_exact_priced_contract_resolver import (
    AyvensExactPricedContractResolver,
)

TARGET_GROUP = "BYD::ATTO 2::PHEV"


def main():
    pair = next(
        item
        for item in MarketMatchEngine().build()
        if item.group_key == TARGET_GROUP
    )

    print("=" * 100)
    print("LIVE CONTRACT COORDINATE CROSS-CHECK V2")
    print("=" * 100)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        try:
            print()
            print("--- ARVAL AT AYVENS COORDINATE ---")
            arval = ArvalContractVariantObserver(browser).observe(
                pair.left_url,
                targets=((pair.right_duration, pair.right_mileage),),
            )
            print("Status:", arval.status)
            print("Diagnostic:", arval.diagnostic)
            for item in arval.observations:
                print(item.duration, item.mileage, item.monthly_fee, item.source_text)

            print()
            print("--- AYVENS AT ARVAL COORDINATE ---")
            ayvens = AyvensExactPricedContractResolver(browser).resolve(
                pair.right_url,
                targets=((pair.left_duration, pair.left_mileage),),
            )
            print("Status:", ayvens.status)
            print("Diagnostic:", ayvens.diagnostic)
            for item in ayvens.observations:
                print(
                    item.duration,
                    item.mileage,
                    item.monthly_fee,
                    item.evidence_method,
                    item.source_text,
                )
        finally:
            browser.close()

    print()
    print(
        "DIAGNOSTIC COMPLETE - ONLY OPPOSITE-SIDE "
        "OBSERVED COORDINATES WERE REQUESTED."
    )


if __name__ == "__main__":
    main()
