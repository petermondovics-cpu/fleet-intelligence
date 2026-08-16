from dataclasses import dataclass
from typing import Optional, Tuple

from market_intelligence.comparable_offer_groups import (
    MATCH_EXACT,
    MATCH_NEEDS_EVIDENCE,
    MATCH_NORMALIZABLE,
    ComparableOfferGroup,
    ComparableOfferGroupService,
    ComparableOfferMember,
)


PAIR_EXACT = "EXACT_PAIR"
PAIR_NORMALIZABLE = "NORMALIZABLE_PAIR"
PAIR_NEEDS_EVIDENCE = "NEEDS_EVIDENCE_PAIR"
PAIR_BLOCKED = "BLOCKED_PAIR"


@dataclass(frozen=True)
class MarketOfferPair:
    pair_key: str

    group_key: str
    brand: str
    model: str
    fuel_type: str

    left_provider: str
    right_provider: str

    left_offer_id: str
    right_offer_id: str

    left_monthly_fee: Optional[int]
    right_monthly_fee: Optional[int]

    left_duration: Optional[int]
    right_duration: Optional[int]

    left_mileage: Optional[int]
    right_mileage: Optional[int]

    left_trim: Optional[str]
    right_trim: Optional[str]

    left_url: Optional[str]
    right_url: Optional[str]

    contract_exact: bool
    duration_exact: bool
    mileage_exact: bool
    trim_exact: bool

    pair_status: str

    full_comparison_candidate: bool
    price_comparison_allowed: bool

    diagnostic: str


class MarketMatchEngine:
    """
    Market Match Engine V1.

    Converts conservative cross-provider vehicle groups into explicit
    provider-to-provider offer pairs.

    Safety rules:
    - only pairs from the same ComparableOfferGroup are created;
    - same-provider pairs are never created;
    - price winner is never calculated here;
    - price_comparison_allowed is always False in V1;
    - NORMALIZABLE means only that contract coordinates may be normalized;
    - trim/service/equipment/financial equivalence is NOT inferred;
    - duplicate directional pairs are avoided.
    """

    def __init__(
        self,
        group_service=None,
    ):
        self.group_service = (
            group_service
            or ComparableOfferGroupService()
        )

    def build(
        self,
    ) -> Tuple[MarketOfferPair, ...]:

        groups = self.group_service.build()

        pairs = []

        for group in groups:
            pairs.extend(
                self._pairs_for_group(
                    group
                )
            )

        pairs.sort(
            key=lambda pair: (
                pair.brand,
                pair.model,
                pair.fuel_type,
                pair.left_provider,
                pair.right_provider,
                pair.left_offer_id,
                pair.right_offer_id,
            )
        )

        return tuple(pairs)

    # ========================================================
    # GROUP -> PAIRS
    # ========================================================

    def _pairs_for_group(
        self,
        group: ComparableOfferGroup,
    ):

        members = group.members
        out = []

        for i, left in enumerate(members):
            for right in members[i + 1:]:

                if (
                    left.provider
                    == right.provider
                ):
                    continue

                ordered_left, ordered_right = (
                    self._provider_order(
                        left,
                        right,
                    )
                )

                out.append(
                    self._build_pair(
                        group,
                        ordered_left,
                        ordered_right,
                    )
                )

        return out

    def _build_pair(
        self,
        group: ComparableOfferGroup,
        left: ComparableOfferMember,
        right: ComparableOfferMember,
    ) -> MarketOfferPair:

        duration_exact = (
            left.duration is not None
            and right.duration is not None
            and left.duration == right.duration
        )

        mileage_exact = (
            left.mileage is not None
            and right.mileage is not None
            and left.mileage == right.mileage
        )

        contract_exact = (
            duration_exact
            and mileage_exact
        )

        trim_exact = self._same_text(
            left.trim,
            right.trim,
        )

        pair_status, candidate, diagnostic = (
            self._status(
                group,
                left,
                right,
                contract_exact,
                trim_exact,
            )
        )

        return MarketOfferPair(
            pair_key=self._pair_key(
                group.group_key,
                left.offer_id,
                right.offer_id,
            ),
            group_key=group.group_key,
            brand=group.brand,
            model=group.model,
            fuel_type=group.fuel_type,
            left_provider=left.provider,
            right_provider=right.provider,
            left_offer_id=left.offer_id,
            right_offer_id=right.offer_id,
            left_monthly_fee=left.monthly_fee,
            right_monthly_fee=right.monthly_fee,
            left_duration=left.duration,
            right_duration=right.duration,
            left_mileage=left.mileage,
            right_mileage=right.mileage,
            left_trim=left.trim,
            right_trim=right.trim,
            left_url=left.url,
            right_url=right.url,
            contract_exact=contract_exact,
            duration_exact=duration_exact,
            mileage_exact=mileage_exact,
            trim_exact=trim_exact,
            pair_status=pair_status,
            full_comparison_candidate=candidate,
            price_comparison_allowed=False,
            diagnostic=diagnostic,
        )

    # ========================================================
    # STATUS
    # ========================================================

    @staticmethod
    def _status(
        group,
        left,
        right,
        contract_exact,
        trim_exact,
    ):

        if (
            left.monthly_fee is None
            or right.monthly_fee is None
        ):
            return (
                PAIR_BLOCKED,
                False,
                (
                    "At least one offer has no observed monthly fee. "
                    "Pair cannot proceed to comparison."
                ),
            )

        if (
            left.duration is None
            or right.duration is None
            or left.mileage is None
            or right.mileage is None
        ):
            return (
                PAIR_NEEDS_EVIDENCE,
                False,
                (
                    "Canonical vehicle family matches, but contract "
                    "coordinates are incomplete."
                ),
            )

        if group.match_status == MATCH_EXACT:
            if trim_exact:
                return (
                    PAIR_EXACT,
                    True,
                    (
                        "Canonical vehicle family, published trim, "
                        "duration and mileage match. Full evidence-aware "
                        "comparison is still required before price ranking."
                    ),
                )

            return (
                PAIR_NEEDS_EVIDENCE,
                True,
                (
                    "Canonical vehicle family and contract coordinates "
                    "match, but trim equivalence is not established."
                ),
            )

        if group.match_status == MATCH_NORMALIZABLE:
            return (
                PAIR_NORMALIZABLE,
                True,
                (
                    "Canonical vehicle family matches and both contract "
                    "coordinates are observed, but duration and/or mileage "
                    "differ. Contract normalization is required before any "
                    "price comparison."
                ),
            )

        if group.match_status == MATCH_NEEDS_EVIDENCE:
            return (
                PAIR_NEEDS_EVIDENCE,
                True,
                (
                    "Canonical vehicle family matches, but additional "
                    "identity/trim evidence is required before equivalence "
                    "can be established."
                ),
            )

        return (
            PAIR_BLOCKED,
            False,
            (
                "Pair is not safe to promote to the full comparison "
                "pipeline."
            ),
        )

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _provider_order(
        left,
        right,
    ):
        # Stable deterministic orientation.
        if (
            left.provider.casefold(),
            left.offer_id,
        ) <= (
            right.provider.casefold(),
            right.offer_id,
        ):
            return left, right

        return right, left

    @staticmethod
    def _same_text(
        left,
        right,
    ) -> bool:

        if left is None or right is None:
            return False

        return (
            str(left).strip().casefold()
            == str(right).strip().casefold()
        )

    @staticmethod
    def _pair_key(
        group_key,
        left_offer_id,
        right_offer_id,
    ) -> str:

        return (
            f"{group_key}"
            f"::{left_offer_id}"
            f"::{right_offer_id}"
        )
