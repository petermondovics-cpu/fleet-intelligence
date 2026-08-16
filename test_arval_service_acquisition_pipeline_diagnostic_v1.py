from market_intelligence.market_match_engine import (
    MarketMatchEngine,
)
from market_intelligence.market_pair_full_comparison_bridge import (
    MarketPairFullComparisonBridge,
)


TARGET_GROUP = "BYD::ATTO 2::PHEV"


def main():
    print("=" * 100)
    print("ARVAL SERVICE ACQUISITION PIPELINE DIAGNOSTIC V1")
    print("=" * 100)

    pair = next(
        (
            p
            for p in MarketMatchEngine().build()
            if p.group_key == TARGET_GROUP
        ),
        None,
    )

    assert pair is not None

    result = (
        MarketPairFullComparisonBridge()
        .evaluate(
            pair,
            headless=False,
        )
    )

    print()
    print("Bridge status:", result.status)
    print("Diagnostic:", result.diagnostic)

    acquisition = result.acquisition

    if acquisition is None:
        print("NO ACQUISITION RESULT")
        return

    execution = getattr(
        acquisition,
        "execution",
        acquisition,
    )

    candidates = getattr(
        execution,
        "candidates",
        (),
    )

    print()
    print("--- ALL ACQUISITION CANDIDATES ---")
    print("Count:", len(candidates))

    for idx, c in enumerate(
        candidates,
        start=1,
    ):
        print()
        print("CANDIDATE", idx)
        print("provider:", getattr(c, "provider", None))
        print(
            "dimension:",
            getattr(c, "target_dimension", None),
        )
        print(
            "action:",
            getattr(c, "action_type", None),
        )
        print(
            "status:",
            getattr(c, "status", None),
        )
        print(
            "candidate_type:",
            getattr(c, "candidate_type", None),
        )
        print(
            "source_type:",
            getattr(c, "source_type", None),
        )
        print(
            "source_url:",
            getattr(c, "source_url", None),
        )
        print(
            "diagnostic:",
            getattr(c, "diagnostic", None),
        )

        payload = getattr(
            c,
            "payload",
            {},
        ) or {}

        print(
            "scope:",
            payload.get("applicability_scope"),
        )
        print(
            "method:",
            payload.get("evidence_method"),
        )

        services = payload.get("services") or ()

        print(
            "service codes:",
            tuple(
                item.get("code")
                for item in services
                if isinstance(item, dict)
            ),
        )

    print()
    print("--- ARVAL SERVICE CANDIDATES ONLY ---")

    arval_services = [
        c
        for c in candidates
        if (
            getattr(c, "provider", "")
            .strip()
            .casefold()
            == "arval"
            and getattr(
                c,
                "target_dimension",
                "",
            )
            == "SERVICES"
        )
    ]

    print(
        "Arval service candidate count:",
        len(arval_services),
    )

    for c in arval_services:
        payload = getattr(
            c,
            "payload",
            {},
        ) or {}

        print()
        print(
            "status:",
            getattr(c, "status", None),
        )
        print(
            "source_type:",
            getattr(c, "source_type", None),
        )
        print(
            "scope:",
            payload.get("applicability_scope"),
        )
        print(
            "services:",
            payload.get("services"),
        )
        print(
            "diagnostic:",
            getattr(c, "diagnostic", None),
        )

    enrichment = result.enrichment

    if enrichment is not None:
        print()
        print("--- ENRICHMENT ---")
        print(
            "LEFT:",
            enrichment.left_services.provider,
            enrichment.left_services.usable_status,
            enrichment.left_services.acquisition_used,
            enrichment.left_services.acquired_codes,
            enrichment.left_services.diagnostic,
        )
        print(
            "RIGHT:",
            enrichment.right_services.provider,
            enrichment.right_services.usable_status,
            enrichment.right_services.acquisition_used,
            enrichment.right_services.acquired_codes,
            enrichment.right_services.diagnostic,
        )

    print()
    print("=" * 100)
    print(
        "DIAGNOSTIC COMPLETE - NO PIPELINE BEHAVIOR WAS CHANGED."
    )


if __name__ == "__main__":
    main()
