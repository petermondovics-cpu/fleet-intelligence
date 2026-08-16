from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple


OBSERVED = "OBSERVED"
UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class ObservedAyvensContractPrice:
    duration: int
    mileage: int
    monthly_fee: int
    source_text: str
    evidence_method: str


@dataclass(frozen=True)
class AyvensExactPricedContractResult:
    status: str
    provider: str
    source_url: str
    observations: Tuple[ObservedAyvensContractPrice, ...]
    diagnostic: str


class AyvensExactPricedContractResolver:
    """
    Ayvens Exact Priced Contract Resolver V1.

    Purpose
    -------
    Resolve an exact Ayvens offer at explicitly requested contract
    coordinates such as 60 months / 20,000 km/year.

    Evidence order
    --------------
    1. Exact-offer API:
       Accept ONLY a record that explicitly contains:
       - requested duration,
       - requested annual mileage,
       - a positive monthly price.
    2. Existing exact-offer UI observer:
       If the API has no explicit priced coordinate, fall back to the
       existing AyvensContractVariantObserver.

    Safety
    ------
    - availability/capability metadata alone is never pricing evidence;
    - 36/48/60-month option lists alone are never promoted;
    - no interpolation or duration-price estimation;
    - no reuse of the 48-month price for a 60-month target;
    - no down-payment assumption is made here;
    - ambiguous API records are rejected;
    - absence remains UNRESOLVED.

    The resolver deliberately supports a small set of explicit API field
    aliases because provider JSON field names may differ while semantics
    remain unambiguous. Fuzzy key matching is not used.
    """

    API_ROOT = (
        "https://autotartosberlet.ayvens.com/api/cars"
    )

    DURATION_KEYS = (
        "duration",
        "duration_months",
        "term",
        "term_months",
        "months",
        "contract_duration",
    )

    MILEAGE_KEYS = (
        "mileage",
        "annual_mileage",
        "mileage_per_year",
        "km_per_year",
        "kilometers_per_year",
        "contract_mileage",
    )

    PRICE_KEYS = (
        "monthly_fee",
        "monthly_price",
        "price_monthly",
        "monthly_rental",
        "monthly_rent",
        "rent",
        "price",
    )

    def __init__(self, browser):
        self.browser = browser

    def resolve(
        self,
        url: str,
        *,
        targets: Tuple[Tuple[int, int], ...],
    ) -> AyvensExactPricedContractResult:

        api_url = self._api_url_from_offer(
            url
        )

        api_observations = ()

        if api_url:
            api_observations = (
                self._observe_api(
                    api_url,
                    targets,
                )
            )

        # Exact API-priced states are already provider-owned observations.
        if api_observations:
            return AyvensExactPricedContractResult(
                status=OBSERVED,
                provider="Ayvens",
                source_url=api_url,
                observations=api_observations,
                diagnostic=(
                    "One or more requested Ayvens contract coordinates "
                    "were explicitly priced in the exact-offer provider API."
                ),
            )

        # Fall back to the existing conservative live UI observer.
        try:
            from contract_normalization.ayvens_contract_variant_observer import (
                AyvensContractVariantObserver,
            )

            result = (
                AyvensContractVariantObserver(
                    self.browser
                )
                .observe(
                    url,
                    targets=targets,
                )
            )

            if (
                result.status == OBSERVED
                and result.observations
            ):
                converted = tuple(
                    ObservedAyvensContractPrice(
                        duration=item.duration,
                        mileage=item.mileage,
                        monthly_fee=item.monthly_fee,
                        source_text=item.source_text,
                        evidence_method=(
                            "EXACT_OFFER_UI_STATE"
                        ),
                    )
                    for item in result.observations
                )

                return AyvensExactPricedContractResult(
                    status=OBSERVED,
                    provider="Ayvens",
                    source_url=url,
                    observations=converted,
                    diagnostic=(
                        "Requested Ayvens contract coordinates were "
                        "directly observed in the exact-offer UI."
                    ),
                )

        except Exception:
            pass

        return AyvensExactPricedContractResult(
            status=UNRESOLVED,
            provider="Ayvens",
            source_url=(
                api_url or url
            ),
            observations=(),
            diagnostic=(
                "No requested Ayvens contract coordinate contained an "
                "explicit monthly price in the exact-offer API, and the "
                "exact-offer UI observer could not safely confirm it. "
                "Capability metadata was not promoted to pricing evidence."
            ),
        )

    def _observe_api(
        self,
        api_url: str,
        targets: Tuple[Tuple[int, int], ...],
    ) -> Tuple[ObservedAyvensContractPrice, ...]:

        page = self.browser.new_page()

        try:
            response = page.request.get(
                api_url,
                timeout=60000,
            )

            if not response.ok:
                return ()

            try:
                payload = response.json()
            except Exception:
                return ()

        finally:
            page.close()

        records = tuple(
            self._walk_dicts(
                payload
            )
        )

        observations = []

        for duration, mileage in targets:

            candidates = []

            for path, record in records:
                coordinate = (
                    self._explicit_coordinate(
                        record
                    )
                )

                if coordinate is None:
                    continue

                d, m, price, price_key = (
                    coordinate
                )

                if (
                    d == duration
                    and m == mileage
                ):
                    candidates.append(
                        (
                            path,
                            price,
                            price_key,
                        )
                    )

            # A single target must not resolve to contradictory prices.
            unique_prices = {
                item[1]
                for item in candidates
            }

            if len(unique_prices) != 1:
                continue

            price = next(
                iter(unique_prices)
            )

            # Retain the shortest path as the most local explicit record.
            path, _, price_key = sorted(
                candidates,
                key=lambda item: len(
                    item[0]
                ),
            )[0]

            observations.append(
                ObservedAyvensContractPrice(
                    duration=duration,
                    mileage=mileage,
                    monthly_fee=price,
                    source_text=(
                        "Observed Ayvens exact-offer API priced contract "
                        f"state at {path}: {duration} hó / "
                        f"{mileage} km/év -> {price} Ft/hó "
                        f"(price field: {price_key})."
                    ),
                    evidence_method=(
                        "EXACT_OFFER_PROVIDER_API"
                    ),
                )
            )

        return tuple(
            observations
        )

    @classmethod
    def _explicit_coordinate(
        cls,
        record: Dict[str, Any],
    ) -> Optional[
        Tuple[int, int, int, str]
    ]:

        duration = cls._first_int(
            record,
            cls.DURATION_KEYS,
        )

        mileage = cls._first_int(
            record,
            cls.MILEAGE_KEYS,
        )

        price_result = (
            cls._first_positive_int_with_key(
                record,
                cls.PRICE_KEYS,
            )
        )

        if (
            duration is None
            or mileage is None
            or price_result is None
        ):
            return None

        price, price_key = (
            price_result
        )

        if not (
            12 <= duration <= 84
        ):
            return None

        if not (
            5000 <= mileage <= 100000
        ):
            return None

        if not (
            10000 <= price <= 5000000
        ):
            return None

        return (
            duration,
            mileage,
            price,
            price_key,
        )

    @staticmethod
    def _walk_dicts(
        node: Any,
        path: str = "$",
    ) -> Iterable[
        Tuple[str, Dict[str, Any]]
    ]:

        if isinstance(node, dict):
            yield (
                path,
                node,
            )

            for key, value in node.items():
                yield from (
                    AyvensExactPricedContractResolver
                    ._walk_dicts(
                        value,
                        f"{path}.{key}",
                    )
                )

        elif isinstance(node, list):
            for index, value in enumerate(
                node
            ):
                yield from (
                    AyvensExactPricedContractResolver
                    ._walk_dicts(
                        value,
                        f"{path}[{index}]",
                    )
                )

    @classmethod
    def _first_int(
        cls,
        record: Dict[str, Any],
        keys,
    ) -> Optional[int]:

        lowered = {
            str(k).casefold(): v
            for k, v in record.items()
        }

        for key in keys:
            if key not in lowered:
                continue

            value = cls._coerce_int(
                lowered[key]
            )

            if value is not None:
                return value

        return None

    @classmethod
    def _first_positive_int_with_key(
        cls,
        record: Dict[str, Any],
        keys,
    ) -> Optional[
        Tuple[int, str]
    ]:

        lowered = {
            str(k).casefold(): (
                k,
                v,
            )
            for k, v in record.items()
        }

        for key in keys:
            if key not in lowered:
                continue

            original_key, raw = (
                lowered[key]
            )

            value = cls._coerce_int(
                raw
            )

            if (
                value is not None
                and value > 0
            ):
                return (
                    value,
                    str(original_key),
                )

        return None

    @staticmethod
    def _coerce_int(
        value,
    ) -> Optional[int]:

        if isinstance(
            value,
            bool,
        ):
            return None

        if isinstance(
            value,
            int,
        ):
            return value

        if isinstance(
            value,
            float,
        ):
            if value.is_integer():
                return int(value)
            return None

        if isinstance(
            value,
            str,
        ):
            digits = "".join(
                ch
                for ch in value
                if ch.isdigit()
            )

            if not digits:
                return None

            try:
                return int(digits)
            except ValueError:
                return None

        return None

    @classmethod
    def _api_url_from_offer(
        cls,
        url: str,
    ) -> Optional[str]:

        marker = (
            "autotartosberlet.ayvens.com/"
        )

        if marker not in (
            url or ""
        ):
            return None

        path = (
            url.split(marker, 1)[1]
            .split("?", 1)[0]
            .split("#", 1)[0]
            .strip("/")
        )

        parts = [
            item
            for item in path.split("/")
            if item
        ]

        if len(parts) != 2:
            return None

        return (
            f"{cls.API_ROOT}/"
            f"{parts[0]}/"
            f"{parts[1]}"
        )
