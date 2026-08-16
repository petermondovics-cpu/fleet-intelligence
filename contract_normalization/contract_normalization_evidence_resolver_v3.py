from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from contract_normalization.provider_contract_state_discovery_v1 import (
    ProviderContractStateDiscoveryV1,
)

RESOLVED = "RESOLVED"
UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class ExplicitContractPriceV3:
    provider: str
    duration: int
    mileage: int
    monthly_fee: int
    source_url: str
    source_text: str
    evidence_method: str


@dataclass(frozen=True)
class CommonContractCoordinateV3:
    duration: int
    mileage: int
    left: ExplicitContractPriceV3
    right: ExplicitContractPriceV3


@dataclass(frozen=True)
class ContractNormalizationEvidenceResultV3:
    status: str
    left_provider: str
    right_provider: str
    attempted_coordinates: Tuple[Tuple[int, int], ...]
    left_observations: Tuple[ExplicitContractPriceV3, ...]
    right_observations: Tuple[ExplicitContractPriceV3, ...]
    common_coordinates: Tuple[CommonContractCoordinateV3, ...]
    selected_coordinate: Optional[CommonContractCoordinateV3]
    diagnostic: str

    @property
    def normalized_price_available(self):
        return self.selected_coordinate is not None

    @property
    def normalized_monthly_fee_left(self):
        return None if self.selected_coordinate is None else self.selected_coordinate.left.monthly_fee

    @property
    def normalized_monthly_fee_right(self):
        return None if self.selected_coordinate is None else self.selected_coordinate.right.monthly_fee


class ContractNormalizationEvidenceResolverV3:
    """
    Multi-coordinate evidence closure.

    V3 expands the attempted set beyond the two current states, but still
    resolves only when both providers explicitly price the exact same
    duration/mileage coordinate.
    """

    DEFAULT_DURATIONS = (36, 48, 60)

    def __init__(self, browser, *, discovery=None):
        self.browser = browser
        self.discovery = discovery or ProviderContractStateDiscoveryV1(browser)

    def resolve(self, left_offer, right_offer):
        left_provider = str(left_offer.provider or "")
        right_provider = str(right_offer.provider or "")

        if {left_provider.casefold(), right_provider.casefold()} != {"arval", "ayvens"}:
            return self._unresolved(
                left_provider, right_provider, (), (), (),
                "V3 currently supports an Arval/Ayvens pair only."
            )

        attempted = self._candidate_coordinates(left_offer, right_offer)

        left_discovery = self.discovery.discover(
            left_offer,
            coordinates=attempted,
        )
        right_discovery = self.discovery.discover(
            right_offer,
            coordinates=attempted,
        )

        left = [self._current_observation(left_offer)]
        right = [self._current_observation(right_offer)]

        left.extend(self._convert(left_discovery.observations))
        right.extend(self._convert(right_discovery.observations))

        left = self._dedupe(left)
        right = self._dedupe(right)

        common = self._common(left, right)
        selected = self._select_common(common, left_offer, right_offer)

        if selected is None:
            return self._unresolved(
                left_provider, right_provider, attempted, left, right,
                (
                    "No exact explicitly priced common contract coordinate was "
                    "observed across the multi-coordinate search. No interpolation, "
                    "extrapolation, provider term factor or capability-to-price "
                    "promotion was used."
                ),
                common=common,
            )

        return ContractNormalizationEvidenceResultV3(
            status=RESOLVED,
            left_provider=left_provider,
            right_provider=right_provider,
            attempted_coordinates=attempted,
            left_observations=left,
            right_observations=right,
            common_coordinates=common,
            selected_coordinate=selected,
            diagnostic=(
                "Explicit common priced contract state resolved at "
                f"{selected.duration} months / {selected.mileage} km/year."
            ),
        )

    @classmethod
    def _candidate_coordinates(cls, left_offer, right_offer):
        mileages = tuple(dict.fromkeys((
            int(left_offer.mileage),
            int(right_offer.mileage),
        )))
        durations = tuple(dict.fromkeys((
            int(left_offer.duration),
            int(right_offer.duration),
            *cls.DEFAULT_DURATIONS,
        )))
        return tuple(
            (duration, mileage)
            for mileage in mileages
            for duration in durations
            if 12 <= duration <= 84 and 5000 <= mileage <= 100000
        )

    @staticmethod
    def _current_observation(offer):
        fee = int(offer.monthly_fee)
        if fee <= 0:
            raise ValueError("Current offer monthly fee must be positive.")
        return ExplicitContractPriceV3(
            provider=str(offer.provider),
            duration=int(offer.duration),
            mileage=int(offer.mileage),
            monthly_fee=fee,
            source_url=str(offer.url or ""),
            source_text=(
                f"Observed current exact offer state: {offer.duration} months / "
                f"{offer.mileage} km/year -> {offer.monthly_fee} Ft/month."
            ),
            evidence_method="CURRENT_EXACT_OFFER",
        )

    @staticmethod
    def _convert(items):
        return tuple(
            ExplicitContractPriceV3(
                provider=item.provider,
                duration=item.duration,
                mileage=item.mileage,
                monthly_fee=item.monthly_fee,
                source_url=item.source_url,
                source_text=item.source_text,
                evidence_method=item.evidence_method,
            )
            for item in items
        )

    @staticmethod
    def _dedupe(items):
        by_coord: Dict[Tuple[int, int], ExplicitContractPriceV3] = {}
        conflicts = set()
        for item in items:
            key = (item.duration, item.mileage)
            old = by_coord.get(key)
            if old is None:
                by_coord[key] = item
            elif old.monthly_fee != item.monthly_fee:
                conflicts.add(key)
        return tuple(
            item for key, item in by_coord.items()
            if key not in conflicts
        )

    @staticmethod
    def _common(left, right):
        lmap = {(x.duration, x.mileage): x for x in left}
        rmap = {(x.duration, x.mileage): x for x in right}
        return tuple(
            CommonContractCoordinateV3(coord[0], coord[1], lmap[coord], rmap[coord])
            for coord in sorted(set(lmap) & set(rmap))
        )

    @staticmethod
    def _select_common(common, left_offer, right_offer):
        preferred = (
            (int(left_offer.duration), int(left_offer.mileage)),
            (int(right_offer.duration), int(right_offer.mileage)),
        )
        for coord in preferred:
            for item in common:
                if (item.duration, item.mileage) == coord:
                    return item
        return common[0] if common else None

    @staticmethod
    def _unresolved(lp, rp, attempted, left, right, diagnostic, *, common=()):
        return ContractNormalizationEvidenceResultV3(
            UNRESOLVED, lp, rp, tuple(attempted), tuple(left), tuple(right),
            tuple(common), None, diagnostic
        )
