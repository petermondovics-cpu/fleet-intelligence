from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from market_intelligence.market_offer_repository import (
    MarketOfferRepository,
    MarketOfferRow,
)


MATCH_EXACT = "EXACT"
MATCH_NORMALIZABLE = "NORMALIZABLE"
MATCH_NEEDS_EVIDENCE = "NEEDS_EVIDENCE"
MATCH_NOT_COMPARABLE = "NOT_COMPARABLE"


@dataclass(frozen=True)
class ComparableOfferMember:
    offer_id: str
    provider: str

    brand: Optional[str]
    model: Optional[str]
    trim: Optional[str]
    fuel_type: Optional[str]

    monthly_fee: Optional[int]
    duration: Optional[int]
    mileage: Optional[int]

    url: Optional[str]

    identity_status: Optional[str]
    identity_method: Optional[str]


@dataclass(frozen=True)
class ComparableOfferGroup:
    group_key: str

    brand: str
    model: str
    fuel_type: str

    members: Tuple[ComparableOfferMember, ...]

    providers: Tuple[str, ...]

    provider_count: int
    offer_count: int

    match_status: str

    contract_exact: bool
    duration_values: Tuple[int, ...]
    mileage_values: Tuple[int, ...]

    diagnostic: str


class ComparableOfferGroupService:
    """
    Comparable Offer Groups V1.

    Purpose
    -------
    Build conservative cross-provider market groups from the
    persisted canonical market inventory.

    Important safety rules
    ----------------------
    - no fuzzy matching;
    - brand must match exactly;
    - model must match exactly;
    - fuel type must match exactly;
    - unresolved identity is never promoted;
    - same vehicle family does not imply same trim;
    - different contracts are not silently treated as equal;
    - price winner is NOT calculated here.

    This service answers only:

        "Which offers belong to the same canonical market
        vehicle family, and how comparable are their published
        contract coordinates?"

    Full financial / service / equipment comparability remains
    the responsibility of the evidence-first comparison engine.
    """

    def __init__(
        self,
        repository=None,
    ):
        self.repository = (
            repository
            or MarketOfferRepository()
        )

    def build(
        self,
    ) -> Tuple[ComparableOfferGroup, ...]:

        offers = self.repository.list_offers()

        buckets: Dict[
            Tuple[str, str, str],
            list[MarketOfferRow],
        ] = {}

        for offer in offers:

            key = self._canonical_key(
                offer
            )

            if key is None:
                continue

            buckets.setdefault(
                key,
                [],
            ).append(offer)

        groups = []

        for key, rows in buckets.items():

            providers = tuple(
                sorted({
                    row.provider
                    for row in rows
                    if row.provider
                })
            )

            # Market comparison groups are useful only where
            # at least two providers publish the same canonical
            # vehicle family.
            if len(providers) < 2:
                continue

            group = self._build_group(
                key,
                rows,
                providers,
            )

            groups.append(group)

        groups.sort(
            key=lambda group: (
                group.brand,
                group.model,
                group.fuel_type,
            )
        )

        return tuple(groups)

    # ========================================================
    # GROUP BUILDING
    # ========================================================

    def _build_group(
        self,
        key,
        rows,
        providers,
    ) -> ComparableOfferGroup:

        brand, model, fuel_type = key

        members = tuple(
            self._member(row)
            for row in sorted(
                rows,
                key=lambda row: (
                    row.provider or "",
                    row.duration
                    if row.duration is not None
                    else 999999,
                    row.mileage
                    if row.mileage is not None
                    else 999999999,
                    row.monthly_fee
                    if row.monthly_fee is not None
                    else 999999999,
                    row.id,
                ),
            )
        )

        durations = tuple(
            sorted({
                row.duration
                for row in rows
                if row.duration is not None
            })
        )

        mileages = tuple(
            sorted({
                row.mileage
                for row in rows
                if row.mileage is not None
            })
        )

        contract_complete = all(
            row.duration is not None
            and row.mileage is not None
            for row in rows
        )

        contract_exact = (
            contract_complete
            and len(durations) == 1
            and len(mileages) == 1
        )

        identity_complete = all(
            self._identity_usable(row)
            for row in rows
        )

        trim_values = {
            self._clean(row.trim)
            for row in rows
            if self._clean(row.trim)
        }

        trim_complete = all(
            self._clean(row.trim)
            is not None
            for row in rows
        )

        trim_exact = (
            trim_complete
            and len(trim_values) == 1
        )

        if not identity_complete:

            status = MATCH_NEEDS_EVIDENCE

            diagnostic = (
                "Canonical vehicle family matches across "
                "providers, but at least one offer has "
                "unresolved or unusable identity evidence."
            )

        elif contract_exact and trim_exact:

            status = MATCH_EXACT

            diagnostic = (
                "Canonical vehicle identity, published trim, "
                "duration and mileage match exactly. "
                "Financial, service and equipment evidence "
                "must still be assessed before price ranking."
            )

        elif contract_exact:

            status = MATCH_NEEDS_EVIDENCE

            diagnostic = (
                "Canonical vehicle family and contract "
                "coordinates match, but trim equivalence is "
                "not established."
            )

        elif contract_complete:

            status = MATCH_NORMALIZABLE

            diagnostic = (
                "Canonical vehicle family matches, but "
                "published contract coordinates differ. "
                "Contract normalization is required before "
                "price comparison."
            )

        else:

            status = MATCH_NEEDS_EVIDENCE

            diagnostic = (
                "Canonical vehicle family matches, but "
                "contract evidence is incomplete."
            )

        group_key = self._group_key(
            brand,
            model,
            fuel_type,
        )

        return ComparableOfferGroup(
            group_key=group_key,
            brand=brand,
            model=model,
            fuel_type=fuel_type,
            members=members,
            providers=providers,
            provider_count=len(providers),
            offer_count=len(members),
            match_status=status,
            contract_exact=contract_exact,
            duration_values=durations,
            mileage_values=mileages,
            diagnostic=diagnostic,
        )

    # ========================================================
    # IDENTITY
    # ========================================================

    def _canonical_key(
        self,
        offer: MarketOfferRow,
    ) -> Optional[
        Tuple[str, str, str]
    ]:

        brand = self._clean(
            offer.brand
        )

        model = self._clean(
            offer.model
        )

        fuel = self._clean(
            offer.fuel_type
        )

        if not brand:
            return None

        if not model:
            return None

        if not fuel:
            return None

        return (
            brand,
            model,
            fuel,
        )

    @staticmethod
    def _identity_usable(
        offer: MarketOfferRow,
    ) -> bool:

        status = (
            offer.identity_status
            or ""
        ).upper()

        # Legacy rows may not contain identity status.
        # They remain usable as persisted canonical data,
        # but explicit UNRESOLVED must never be promoted.
        if status == "UNRESOLVED":
            return False

        return bool(
            offer.brand
            and offer.model
            and offer.fuel_type
        )

    # ========================================================
    # MEMBER
    # ========================================================

    @staticmethod
    def _member(
        row: MarketOfferRow,
    ) -> ComparableOfferMember:

        return ComparableOfferMember(
            offer_id=row.id,
            provider=row.provider,
            brand=row.brand,
            model=row.model,
            trim=row.trim,
            fuel_type=row.fuel_type,
            monthly_fee=row.monthly_fee,
            duration=row.duration,
            mileage=row.mileage,
            url=row.url,
            identity_status=row.identity_status,
            identity_method=row.identity_method,
        )

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _clean(
        value: Optional[str],
    ) -> Optional[str]:

        if value is None:
            return None

        cleaned = (
            str(value)
            .strip()
            .upper()
        )

        return cleaned or None

    @staticmethod
    def _group_key(
        brand: str,
        model: str,
        fuel_type: str,
    ) -> str:

        return (
            f"{brand}"
            f"::{model}"
            f"::{fuel_type}"
        )