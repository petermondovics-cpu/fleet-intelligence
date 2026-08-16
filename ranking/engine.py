from dataclasses import dataclass
from typing import Dict, List

from comparison.engine import ComparisonResult


@dataclass
class ProviderRanking:

    provider: str

    # ------------------------------------------------
    # DIRECT COMPARISON
    # ------------------------------------------------

    comparable_comparisons: int
    wins: int

    win_rate: float

    # ------------------------------------------------
    # PRICE ADVANTAGE
    #
    # Only calculated from valid direct wins.
    # ------------------------------------------------

    average_monthly_advantage: float
    average_price_advantage_percent: float

    total_annual_saving: int

    # ------------------------------------------------
    # COMPETITIVE POSITION
    # ------------------------------------------------

    competitive_offers: int
    competitive_rate: float

    # ------------------------------------------------
    # MARKET COVERAGE
    # ------------------------------------------------

    total_comparisons: int

    normalization_required: int

    potential_matches: int

    term_normalization_required: int

    mileage_normalization_required: int

    term_and_mileage_normalization_required: int

    # ------------------------------------------------
    # RANKING STATUS
    # ------------------------------------------------

    ranking_status: str

    # ------------------------------------------------
    # RANK
    #
    # 0 = no valid direct ranking possible
    # ------------------------------------------------

    rank: int = 0


class RankingEngine:

    def rank(
        self,
        comparisons: List[ComparisonResult],
    ) -> List[ProviderRanking]:

        provider_stats: Dict[
            str,
            dict,
        ] = {}

        # ------------------------------------------------
        # STEP 1
        #
        # Build provider universe from ALL comparisons.
        #
        # Important:
        # A provider must remain visible even when
        # there are currently no directly comparable
        # contracts.
        # ------------------------------------------------

        for comparison in comparisons:

            if len(comparison.offers) < 2:
                continue

            provider_names = {
                offer.provider
                for offer in comparison.offers
            }

            for provider in provider_names:

                if provider not in provider_stats:

                    provider_stats[provider] = (
                        self._empty_stats()
                    )

        # ------------------------------------------------
        # STEP 2
        #
        # Analyze every comparison.
        # ------------------------------------------------

        for comparison in comparisons:

            if len(comparison.offers) < 2:
                continue

            provider_names = {
                offer.provider
                for offer in comparison.offers
            }

            # ------------------------------------------------
            # TOTAL COMPARISONS
            # ------------------------------------------------

            for provider in provider_names:

                provider_stats[
                    provider
                ][
                    "total_comparisons"
                ] += 1

            # ------------------------------------------------
            # POTENTIAL MATCH
            #
            # Example:
            #
            # BYD ATTO 3 PHEV
            # vs
            # BYD ATTO 3 EV
            #
            # Market relevance exists,
            # but price winner is invalid.
            # ------------------------------------------------

            if (
                comparison.vehicle_match_type
                == "MODEL_MATCH_POWERTRAIN_MISMATCH"
            ):

                for provider in provider_names:

                    provider_stats[
                        provider
                    ][
                        "potential_matches"
                    ] += 1

                continue

            # ------------------------------------------------
            # DIRECT COMPARISON
            #
            # Must satisfy:
            #
            # 1. Contract comparable
            # 2. Valid price winner
            # 3. Exact vehicle variant
            # ------------------------------------------------

            if (
                comparison.contract_comparable
                and
                comparison.price_winner_is_valid
                and
                comparison.variant_match_type
                == "EXACT_VARIANT"
            ):

                # --------------------------------------------
                # Count comparable comparison for every
                # participating provider.
                # --------------------------------------------

                for provider in provider_names:

                    provider_stats[
                        provider
                    ][
                        "comparable_comparisons"
                    ] += 1

                # --------------------------------------------
                # PRICE WINNER
                # --------------------------------------------

                winner = (
                    comparison.price_winner
                )

                if winner in provider_names:

                    winner_stats = (
                        provider_stats[
                            winner
                        ]
                    )

                    winner_stats[
                        "wins"
                    ] += 1

                    winner_stats[
                        "price_advantages"
                    ].append(
                        comparison.price_difference
                    )

                    winner_stats[
                        "price_advantage_percent"
                    ].append(
                        comparison.price_difference_percent
                    )

                    winner_stats[
                        "annual_saving"
                    ] += (
                        comparison.annual_saving
                    )

                    winner_stats[
                        "competitive_offers"
                    ] += 1

                continue

            # ------------------------------------------------
            # CONTRACT NORMALIZATION REQUIRED
            #
            # Vehicle is comparable, but contract
            # structure is different.
            # ------------------------------------------------

            if not comparison.contract_comparable:

                for provider in provider_names:

                    provider_stats[
                        provider
                    ][
                        "normalization_required"
                    ] += 1

                duration_difference = (
                    self._get_duration_difference(
                        comparison
                    )
                )

                mileage_difference = (
                    self._get_mileage_difference(
                        comparison
                    )
                )

                # --------------------------------------------
                # TERM ONLY
                # --------------------------------------------

                if (
                    duration_difference > 0
                    and
                    mileage_difference == 0
                ):

                    for provider in provider_names:

                        provider_stats[
                            provider
                        ][
                            "term_normalization_required"
                        ] += 1

                # --------------------------------------------
                # MILEAGE ONLY
                # --------------------------------------------

                elif (
                    duration_difference == 0
                    and
                    mileage_difference > 0
                ):

                    for provider in provider_names:

                        provider_stats[
                            provider
                        ][
                            "mileage_normalization_required"
                        ] += 1

                # --------------------------------------------
                # TERM + MILEAGE
                # --------------------------------------------

                elif (
                    duration_difference > 0
                    and
                    mileage_difference > 0
                ):

                    for provider in provider_names:

                        provider_stats[
                            provider
                        ][
                            "term_and_mileage_normalization_required"
                        ] += 1

                continue

        # ------------------------------------------------
        # STEP 3
        #
        # BUILD PROVIDER RESULTS
        # ------------------------------------------------

        rankings = []

        for provider, stats in (
            provider_stats.items()
        ):

            comparable = (
                stats[
                    "comparable_comparisons"
                ]
            )

            wins = (
                stats[
                    "wins"
                ]
            )

            # ------------------------------------------------
            # WIN RATE
            # ------------------------------------------------

            if comparable > 0:

                win_rate = (
                    wins
                    / comparable
                    * 100
                )

                competitive_rate = (
                    stats[
                        "competitive_offers"
                    ]
                    / comparable
                    * 100
                )

            else:

                win_rate = 0.0

                competitive_rate = 0.0

            # ------------------------------------------------
            # MONTHLY ADVANTAGE
            # ------------------------------------------------

            advantages = (
                stats[
                    "price_advantages"
                ]
            )

            if advantages:

                average_monthly_advantage = (
                    sum(advantages)
                    / len(advantages)
                )

            else:

                average_monthly_advantage = 0.0

            # ------------------------------------------------
            # PRICE ADVANTAGE %
            # ------------------------------------------------

            advantage_percent = (
                stats[
                    "price_advantage_percent"
                ]
            )

            if advantage_percent:

                average_price_advantage_percent = (
                    sum(
                        advantage_percent
                    )
                    / len(
                        advantage_percent
                    )
                )

            else:

                average_price_advantage_percent = 0.0

            # ------------------------------------------------
            # RANKING STATUS
            # ------------------------------------------------

            if comparable == 0:

                ranking_status = (
                    "INSUFFICIENT_DIRECT_DATA"
                )

            elif wins == comparable:

                ranking_status = (
                    "LEADING"
                )

            elif wins > 0:

                ranking_status = (
                    "COMPETITIVE"
                )

            else:

                ranking_status = (
                    "NO_DIRECT_WINS"
                )

            # ------------------------------------------------
            # RESULT
            # ------------------------------------------------

            rankings.append(
                ProviderRanking(

                    provider=provider,

                    comparable_comparisons=(
                        comparable
                    ),

                    wins=wins,

                    win_rate=round(
                        win_rate,
                        2,
                    ),

                    average_monthly_advantage=round(
                        average_monthly_advantage,
                        2,
                    ),

                    average_price_advantage_percent=round(
                        average_price_advantage_percent,
                        2,
                    ),

                    total_annual_saving=(
                        stats[
                            "annual_saving"
                        ]
                    ),

                    competitive_offers=(
                        stats[
                            "competitive_offers"
                        ]
                    ),

                    competitive_rate=round(
                        competitive_rate,
                        2,
                    ),

                    total_comparisons=(
                        stats[
                            "total_comparisons"
                        ]
                    ),

                    normalization_required=(
                        stats[
                            "normalization_required"
                        ]
                    ),

                    potential_matches=(
                        stats[
                            "potential_matches"
                        ]
                    ),

                    term_normalization_required=(
                        stats[
                            "term_normalization_required"
                        ]
                    ),

                    mileage_normalization_required=(
                        stats[
                            "mileage_normalization_required"
                        ]
                    ),

                    term_and_mileage_normalization_required=(
                        stats[
                            "term_and_mileage_normalization_required"
                        ]
                    ),

                    ranking_status=(
                        ranking_status
                    ),
                )
            )

        # ------------------------------------------------
        # STEP 4
        #
        # SORT
        #
        # Providers with direct data come first.
        #
        # Within ranked providers:
        #   1. Win rate
        #   2. Wins
        #   3. Average price advantage %
        #
        # Providers without direct data remain visible
        # but receive rank 0.
        # ------------------------------------------------

        rankings.sort(
            key=lambda result: (
                result.comparable_comparisons > 0,
                result.win_rate,
                result.wins,
                result.average_price_advantage_percent,
            ),
            reverse=True,
        )

        # ------------------------------------------------
        # STEP 5
        #
        # ASSIGN RANKS
        # ------------------------------------------------

        rank = 1

        for result in rankings:

            if (
                result.comparable_comparisons
                > 0
            ):

                result.rank = rank

                rank += 1

            else:

                result.rank = 0

        return rankings

    # ------------------------------------------------
    # EMPTY PROVIDER STATS
    # ------------------------------------------------

    def _empty_stats(
        self,
    ) -> dict:

        return {

            "total_comparisons": 0,

            "comparable_comparisons": 0,

            "wins": 0,

            "price_advantages": [],

            "price_advantage_percent": [],

            "annual_saving": 0,

            "competitive_offers": 0,

            "normalization_required": 0,

            "potential_matches": 0,

            "term_normalization_required": 0,

            "mileage_normalization_required": 0,

            "term_and_mileage_normalization_required": 0,
        }

    # ------------------------------------------------
    # DURATION DIFFERENCE
    # ------------------------------------------------

    def _get_duration_difference(
        self,
        comparison: ComparisonResult,
    ) -> int:

        if len(comparison.offers) < 2:

            return 0

        offer_a = (
            comparison.offers[0]
        )

        offer_b = (
            comparison.offers[1]
        )

        return abs(
            offer_a.duration
            - offer_b.duration
        )

    # ------------------------------------------------
    # MILEAGE DIFFERENCE
    # ------------------------------------------------

    def _get_mileage_difference(
        self,
        comparison: ComparisonResult,
    ) -> int:

        if len(comparison.offers) < 2:

            return 0

        offer_a = (
            comparison.offers[0]
        )

        offer_b = (
            comparison.offers[1]
        )

        return abs(
            offer_a.mileage
            - offer_b.mileage
        )