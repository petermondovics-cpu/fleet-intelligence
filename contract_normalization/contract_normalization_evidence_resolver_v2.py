from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from contract_normalization.arval_contract_variant_observer import (
    OBSERVED as ARVAL_OBSERVED,
    ArvalContractVariantObserver,
)
from contract_normalization.ayvens_exact_priced_contract_resolver import (
    OBSERVED as AYVENS_OBSERVED,
    AyvensExactPricedContractResolver,
)

RESOLVED = "RESOLVED"
UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class ExplicitContractPrice:
    provider: str
    duration: int
    mileage: int
    monthly_fee: int
    source_url: str
    source_text: str
    evidence_method: str


@dataclass(frozen=True)
class CommonContractCoordinate:
    duration: int
    mileage: int
    left: ExplicitContractPrice
    right: ExplicitContractPrice


@dataclass(frozen=True)
class ContractNormalizationEvidenceResult:
    status: str
    left_provider: str
    right_provider: str
    attempted_coordinates: Tuple[Tuple[int, int], ...]
    left_observations: Tuple[ExplicitContractPrice, ...]
    right_observations: Tuple[ExplicitContractPrice, ...]
    common_coordinates: Tuple[CommonContractCoordinate, ...]
    selected_coordinate: Optional[CommonContractCoordinate]
    diagnostic: str

    @property
    def normalized_price_available(self) -> bool:
        return self.selected_coordinate is not None

    @property
    def normalized_monthly_fee_left(self) -> Optional[int]:
        if self.selected_coordinate is None:
            return None
        return self.selected_coordinate.left.monthly_fee

    @property
    def normalized_monthly_fee_right(self) -> Optional[int]:
        if self.selected_coordinate is None:
            return None
        return self.selected_coordinate.right.monthly_fee


class ContractNormalizationEvidenceResolverV2:
    """
    Resolve only explicitly priced common contract coordinates.

    V2 safety:
    - current exact-offer states seed evidence;
    - only the two currently observed coordinates are attempted;
    - Arval alternatives come only from ArvalContractVariantObserver;
    - Ayvens alternatives come only from AyvensExactPricedContractResolver;
    - no interpolation, extrapolation or provider term factor;
    - capability metadata alone never becomes pricing evidence;
    - one-sided priced states remain unresolved.
    """

    def __init__(
        self,
        browser,
        *,
        arval_observer=None,
        ayvens_resolver=None,
    ):
        self.browser = browser
        self.arval_observer = (
            arval_observer
            or ArvalContractVariantObserver(browser)
        )
        self.ayvens_resolver = (
            ayvens_resolver
            or AyvensExactPricedContractResolver(browser)
        )

    def resolve(self, left_offer, right_offer) -> ContractNormalizationEvidenceResult:
        left_provider = str(left_offer.provider or "")
        right_provider = str(right_offer.provider or "")

        if {
            left_provider.casefold(),
            right_provider.casefold(),
        } != {"arval", "ayvens"}:
            return self._unresolved(
                left_provider,
                right_provider,
                (),
                (),
                (),
                "V2 currently supports an Arval/Ayvens pair only.",
            )

        attempted = self._candidate_coordinates(left_offer, right_offer)

        left = [self._current_observation(left_offer)]
        right = [self._current_observation(right_offer)]

        left_current = (int(left_offer.duration), int(left_offer.mileage))
        right_current = (int(right_offer.duration), int(right_offer.mileage))

        left_targets = tuple(c for c in attempted if c != left_current)
        right_targets = tuple(c for c in attempted if c != right_current)

        if left_provider.casefold() == "arval":
            left.extend(self._observe_arval(left_offer.url, left_targets))
            right.extend(self._observe_ayvens(right_offer.url, right_targets))
        else:
            left.extend(self._observe_ayvens(left_offer.url, left_targets))
            right.extend(self._observe_arval(right_offer.url, right_targets))

        left = self._dedupe(left)
        right = self._dedupe(right)

        common = self._common(left, right)
        selected = self._select_common(common, left_offer, right_offer)

        if selected is None:
            return self._unresolved(
                left_provider,
                right_provider,
                attempted,
                left,
                right,
                (
                    "No exact priced contract coordinate was explicitly observed "
                    "for both providers. One-sided priced states and provider "
                    "capability metadata were not promoted."
                ),
                common=common,
            )

        return ContractNormalizationEvidenceResult(
            status=RESOLVED,
            left_provider=left_provider,
            right_provider=right_provider,
            attempted_coordinates=attempted,
            left_observations=tuple(left),
            right_observations=tuple(right),
            common_coordinates=tuple(common),
            selected_coordinate=selected,
            diagnostic=(
                "Both providers have explicit monthly prices at the same "
                f"contract coordinate: {selected.duration} months / "
                f"{selected.mileage} km/year."
            ),
        )

    @staticmethod
    def _candidate_coordinates(left_offer, right_offer) -> Tuple[Tuple[int, int], ...]:
        raw = (
            (int(left_offer.duration), int(left_offer.mileage)),
            (int(right_offer.duration), int(right_offer.mileage)),
        )
        return tuple(dict.fromkeys(raw))

    @staticmethod
    def _current_observation(offer) -> ExplicitContractPrice:
        fee = int(offer.monthly_fee)
        if fee <= 0:
            raise ValueError("Current offer monthly fee must be positive.")

        return ExplicitContractPrice(
            provider=str(offer.provider),
            duration=int(offer.duration),
            mileage=int(offer.mileage),
            monthly_fee=fee,
            source_url=str(offer.url or ""),
            source_text=(
                "Observed current exact offer state: "
                f"{offer.duration} months / {offer.mileage} km/year -> "
                f"{offer.monthly_fee} Ft/month."
            ),
            evidence_method="CURRENT_EXACT_OFFER",
        )

    def _observe_arval(self, url, targets):
        if not targets:
            return ()
        try:
            result = self.arval_observer.observe(url, targets=targets)
        except Exception:
            return ()
        if result.status != ARVAL_OBSERVED:
            return ()

        return tuple(
            ExplicitContractPrice(
                provider="Arval",
                duration=int(item.duration),
                mileage=int(item.mileage),
                monthly_fee=int(item.monthly_fee),
                source_url=result.source_url,
                source_text=item.source_text,
                evidence_method="EXACT_OFFER_UI_STATE",
            )
            for item in result.observations
            if int(item.monthly_fee) > 0
        )

    def _observe_ayvens(self, url, targets):
        if not targets:
            return ()
        try:
            result = self.ayvens_resolver.resolve(url, targets=targets)
        except Exception:
            return ()
        if result.status != AYVENS_OBSERVED:
            return ()

        return tuple(
            ExplicitContractPrice(
                provider="Ayvens",
                duration=int(item.duration),
                mileage=int(item.mileage),
                monthly_fee=int(item.monthly_fee),
                source_url=result.source_url,
                source_text=item.source_text,
                evidence_method=item.evidence_method,
            )
            for item in result.observations
            if int(item.monthly_fee) > 0
        )

    @staticmethod
    def _dedupe(items):
        by_key: Dict[Tuple[int, int, int], ExplicitContractPrice] = {}
        for item in items:
            by_key.setdefault(
                (item.duration, item.mileage, item.monthly_fee),
                item,
            )
        return tuple(by_key.values())

    @staticmethod
    def _common(left, right):
        lmap = {(item.duration, item.mileage): item for item in left}
        rmap = {(item.duration, item.mileage): item for item in right}

        return tuple(
            CommonContractCoordinate(
                duration=coord[0],
                mileage=coord[1],
                left=lmap[coord],
                right=rmap[coord],
            )
            for coord in sorted(set(lmap) & set(rmap))
        )

    @staticmethod
    def _select_common(common, left_offer, right_offer):
        if not common:
            return None

        preferred = (
            (int(left_offer.duration), int(left_offer.mileage)),
            (int(right_offer.duration), int(right_offer.mileage)),
        )

        for coord in preferred:
            for item in common:
                if (item.duration, item.mileage) == coord:
                    return item

        return common[0]

    @staticmethod
    def _unresolved(
        left_provider,
        right_provider,
        attempted,
        left,
        right,
        diagnostic,
        *,
        common=(),
    ):
        return ContractNormalizationEvidenceResult(
            status=UNRESOLVED,
            left_provider=left_provider,
            right_provider=right_provider,
            attempted_coordinates=tuple(attempted),
            left_observations=tuple(left),
            right_observations=tuple(right),
            common_coordinates=tuple(common),
            selected_coordinate=None,
            diagnostic=diagnostic,
        )
