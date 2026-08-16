from dataclasses import dataclass
from typing import Dict, Tuple

from contract_normalization.arval_contract_variant_observer import (
    OBSERVED as ARVAL_OBSERVED,
    ArvalContractVariantObserver,
)
from contract_normalization.ayvens_exact_priced_contract_resolver import (
    OBSERVED as AYVENS_OBSERVED,
    AyvensExactPricedContractResolver,
)

OBSERVED = "OBSERVED"
UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class DiscoveredContractPrice:
    provider: str
    duration: int
    mileage: int
    monthly_fee: int
    source_url: str
    source_text: str
    evidence_method: str


@dataclass(frozen=True)
class ProviderContractStateDiscoveryResult:
    status: str
    provider: str
    requested_coordinates: Tuple[Tuple[int, int], ...]
    observations: Tuple[DiscoveredContractPrice, ...]
    diagnostic: str


class ProviderContractStateDiscoveryV1:
    """
    Provider-owned multi-coordinate priced-state discovery.

    Safety:
    - discovers only explicitly requested coordinates;
    - accepts only positive explicitly observed monthly fees;
    - provider capability/option metadata is never promoted to price evidence;
    - no interpolation, extrapolation, term factor or missing-price inference.
    """

    DEFAULT_DURATIONS = (36, 48, 60)
    DEFAULT_MILEAGES = (10000, 15000, 20000, 25000, 30000)

    def __init__(self, browser, *, arval_observer=None, ayvens_resolver=None):
        self.browser = browser
        self.arval_observer = arval_observer or ArvalContractVariantObserver(browser)
        self.ayvens_resolver = ayvens_resolver or AyvensExactPricedContractResolver(browser)

    def discover(
        self,
        offer,
        *,
        coordinates: Tuple[Tuple[int, int], ...] = (),
    ) -> ProviderContractStateDiscoveryResult:
        provider = str(offer.provider or "")
        requested = self._coordinates(offer, coordinates)

        if provider.casefold() == "arval":
            return self._discover_arval(str(offer.url or ""), requested)

        if provider.casefold() == "ayvens":
            return self._discover_ayvens(str(offer.url or ""), requested)

        return ProviderContractStateDiscoveryResult(
            status=UNRESOLVED,
            provider=provider,
            requested_coordinates=requested,
            observations=(),
            diagnostic="Provider is not supported by Contract State Discovery V1.",
        )

    def _discover_arval(self, url, requested):
        try:
            result = self.arval_observer.observe(url, targets=requested)
        except Exception as exc:
            return self._failure("Arval", requested, exc)

        if result.status != ARVAL_OBSERVED:
            return ProviderContractStateDiscoveryResult(
                UNRESOLVED, "Arval", requested, (),
                "No requested Arval coordinate was explicitly priced in the exact-offer UI."
            )

        observations = tuple(
            DiscoveredContractPrice(
                provider="Arval",
                duration=int(item.duration),
                mileage=int(item.mileage),
                monthly_fee=int(item.monthly_fee),
                source_url=str(result.source_url or url),
                source_text=str(item.source_text or ""),
                evidence_method="EXACT_OFFER_UI_STATE",
            )
            for item in result.observations
            if int(item.monthly_fee) > 0
        )
        observations = self._dedupe(observations)

        return ProviderContractStateDiscoveryResult(
            OBSERVED if observations else UNRESOLVED,
            "Arval",
            requested,
            observations,
            (
                f"{len(observations)} explicitly priced Arval contract state(s) observed."
                if observations else
                "Arval returned no safe explicitly priced requested state."
            ),
        )

    def _discover_ayvens(self, url, requested):
        try:
            result = self.ayvens_resolver.resolve(url, targets=requested)
        except Exception as exc:
            return self._failure("Ayvens", requested, exc)

        if result.status != AYVENS_OBSERVED:
            return ProviderContractStateDiscoveryResult(
                UNRESOLVED, "Ayvens", requested, (),
                "No requested Ayvens coordinate was explicitly priced in provider-owned evidence."
            )

        observations = tuple(
            DiscoveredContractPrice(
                provider="Ayvens",
                duration=int(item.duration),
                mileage=int(item.mileage),
                monthly_fee=int(item.monthly_fee),
                source_url=str(result.source_url or url),
                source_text=str(item.source_text or ""),
                evidence_method=str(item.evidence_method or ""),
            )
            for item in result.observations
            if int(item.monthly_fee) > 0
        )
        observations = self._dedupe(observations)

        return ProviderContractStateDiscoveryResult(
            OBSERVED if observations else UNRESOLVED,
            "Ayvens",
            requested,
            observations,
            (
                f"{len(observations)} explicitly priced Ayvens contract state(s) observed."
                if observations else
                "Ayvens returned no safe explicitly priced requested state."
            ),
        )

    @classmethod
    def _coordinates(cls, offer, coordinates):
        if coordinates:
            raw = coordinates
        else:
            current_duration = int(offer.duration)
            current_mileage = int(offer.mileage)
            raw = (
                (current_duration, current_mileage),
                *(
                    (duration, current_mileage)
                    for duration in cls.DEFAULT_DURATIONS
                ),
            )
        clean = []
        for duration, mileage in raw:
            duration = int(duration)
            mileage = int(mileage)
            if 12 <= duration <= 84 and 5000 <= mileage <= 100000:
                clean.append((duration, mileage))
        return tuple(dict.fromkeys(clean))

    @staticmethod
    def _dedupe(items):
        by_coordinate: Dict[Tuple[int, int], DiscoveredContractPrice] = {}
        conflicts = set()
        for item in items:
            key = (item.duration, item.mileage)
            previous = by_coordinate.get(key)
            if previous is None:
                by_coordinate[key] = item
            elif previous.monthly_fee != item.monthly_fee:
                conflicts.add(key)
        return tuple(
            item for key, item in by_coordinate.items()
            if key not in conflicts
        )

    @staticmethod
    def _failure(provider, requested, exc):
        return ProviderContractStateDiscoveryResult(
            status=UNRESOLVED,
            provider=provider,
            requested_coordinates=requested,
            observations=(),
            diagnostic=f"{type(exc).__name__}: {exc}",
        )
