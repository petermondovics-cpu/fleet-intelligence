from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Optional


LIVE_UNCHANGED = "LIVE_UNCHANGED"
LIVE_CHANGED = "LIVE_CHANGED"
OFFER_REPLACED = "OFFER_REPLACED"
OFFER_NO_LONGER_AVAILABLE = "OFFER_NO_LONGER_AVAILABLE"
LIFECYCLE_UNRESOLVED = "LIFECYCLE_UNRESOLVED"


@dataclass(frozen=True)
class HistoricalOfferObservation:
    """
    Immutable historical offer state.

    This object represents what was observed at an earlier point in time.
    A later lifecycle check must never mutate these values.
    """

    offer_key: str
    provider: str
    brand: Optional[str]
    model: Optional[str]
    trim: Optional[str]
    fuel_type: Optional[str]
    monthly_fee: Optional[int]
    duration: Optional[int]
    mileage: Optional[int]
    url: str
    observed_at: Optional[str] = None


@dataclass(frozen=True)
class LiveOfferObservation:
    provider: str
    brand: Optional[str]
    model: Optional[str]
    trim: Optional[str]
    fuel_type: Optional[str]
    monthly_fee: Optional[int]
    duration: Optional[int]
    mileage: Optional[int]
    url: str


@dataclass(frozen=True)
class ExactOfferLifecycleResult:
    status: str
    offer_key: str
    provider: str
    checked_url: str
    final_url: Optional[str]
    http_status: Optional[int]
    checked_at: str

    historical_observed_at: Optional[str]
    historical_monthly_fee: Optional[int]
    live_monthly_fee: Optional[int]
    monthly_fee_delta_huf: Optional[int]

    historical_identity: dict
    live_identity: Optional[dict]

    historical_contract: dict
    live_contract: Optional[dict]

    diagnostic: str

    @property
    def historical_evidence_preserved(self) -> bool:
        return True


class ExactOfferLifecycleResolver:
    """
    Exact Offer Lifecycle Resolver V1.

    Distinguishes lifecycle state from evidence validity.

    Core statuses
    -------------
    LIVE_UNCHANGED
        URL is live, exact identity/contract still matches, and the observed
        monthly fee is unchanged.

    LIVE_CHANGED
        URL is live, exact identity/contract still matches, but an explicitly
        observed commercial field (currently monthly fee) changed.

    OFFER_REPLACED
        URL resolves successfully but now describes a different exact offer
        identity or contract coordinate.

    OFFER_NO_LONGER_AVAILABLE
        Provider returns HTTP 404 or 410 for the historical exact-offer URL.

    LIFECYCLE_UNRESOLVED
        Access/load/parser state is not sufficient to classify safely
        (for example HTTP 403/429/5xx or live parser failure).

    Safety
    ------
    - historical values are immutable input;
    - HTTP 404/410 never erases prior evidence;
    - 403/429/5xx are NOT interpreted as offer removal;
    - price changes are accepted only from a successfully parsed live offer;
    - identity/contract change is OFFER_REPLACED, not LIVE_CHANGED;
    - no fuzzy vehicle matching is performed here.
    """

    def __init__(
        self,
        browser,
        *,
        live_loader: Callable[[Any], Any],
        identity_builder: Optional[Callable[[Any], dict]] = None,
    ):
        self.browser = browser
        self.live_loader = live_loader
        self.identity_builder = (
            identity_builder
            or self._default_identity
        )

    def resolve(
        self,
        historical: HistoricalOfferObservation,
    ) -> ExactOfferLifecycleResult:

        checked_at = self._now()

        page = self.browser.new_page()

        try:
            try:
                response = page.goto(
                    historical.url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
            except Exception as exc:
                return self._unresolved(
                    historical,
                    checked_at=checked_at,
                    final_url=getattr(page, "url", None),
                    http_status=None,
                    diagnostic=(
                        "Exact-offer navigation failed; lifecycle state "
                        f"remains unresolved: {exc}"
                    ),
                )

            http_status = (
                response.status
                if response is not None
                else None
            )

            final_url = page.url

            if http_status in {404, 410}:
                return ExactOfferLifecycleResult(
                    status=OFFER_NO_LONGER_AVAILABLE,
                    offer_key=historical.offer_key,
                    provider=historical.provider,
                    checked_url=historical.url,
                    final_url=final_url,
                    http_status=http_status,
                    checked_at=checked_at,
                    historical_observed_at=historical.observed_at,
                    historical_monthly_fee=historical.monthly_fee,
                    live_monthly_fee=None,
                    monthly_fee_delta_huf=None,
                    historical_identity=self._historical_identity(
                        historical
                    ),
                    live_identity=None,
                    historical_contract=self._historical_contract(
                        historical
                    ),
                    live_contract=None,
                    diagnostic=(
                        f"Historical exact-offer URL now returns HTTP "
                        f"{http_status}. Historical evidence is preserved; "
                        "the current lifecycle state is no longer available."
                    ),
                )

            if (
                http_status is None
                or http_status < 200
                or http_status >= 300
            ):
                return self._unresolved(
                    historical,
                    checked_at=checked_at,
                    final_url=final_url,
                    http_status=http_status,
                    diagnostic=(
                        "Exact-offer URL did not return a safely classifiable "
                        f"success/removal status (HTTP {http_status})."
                    ),
                )

            try:
                page.wait_for_timeout(1200)
                wrapped = self.live_loader(
                    page
                )
                live = self._live_from_loaded(
                    wrapped
                )
            except Exception as exc:
                return self._unresolved(
                    historical,
                    checked_at=checked_at,
                    final_url=final_url,
                    http_status=http_status,
                    diagnostic=(
                        "Exact-offer URL is live, but provider content could "
                        "not be parsed safely; lifecycle state remains "
                        f"unresolved: {exc}"
                    ),
                )

            historical_identity = (
                self._historical_identity(
                    historical
                )
            )

            live_identity = (
                self.identity_builder(
                    live
                )
            )

            historical_contract = (
                self._historical_contract(
                    historical
                )
            )

            live_contract = {
                "duration": live.duration,
                "mileage": live.mileage,
            }

            if (
                live.provider != historical.provider
                or live_identity != historical_identity
                or live_contract != historical_contract
            ):
                return ExactOfferLifecycleResult(
                    status=OFFER_REPLACED,
                    offer_key=historical.offer_key,
                    provider=historical.provider,
                    checked_url=historical.url,
                    final_url=final_url,
                    http_status=http_status,
                    checked_at=checked_at,
                    historical_observed_at=historical.observed_at,
                    historical_monthly_fee=historical.monthly_fee,
                    live_monthly_fee=live.monthly_fee,
                    monthly_fee_delta_huf=None,
                    historical_identity=historical_identity,
                    live_identity=live_identity,
                    historical_contract=historical_contract,
                    live_contract=live_contract,
                    diagnostic=(
                        "Historical URL is reachable, but the live exact-offer "
                        "identity and/or contract coordinate differs. "
                        "Historical evidence is preserved as a separate offer."
                    ),
                )

            delta = self._price_delta(
                historical.monthly_fee,
                live.monthly_fee,
            )

            if delta == 0:
                status = LIVE_UNCHANGED
                diagnostic = (
                    "Exact offer is live with matching identity, contract "
                    "coordinate and monthly fee."
                )
            else:
                status = LIVE_CHANGED
                diagnostic = (
                    "Exact offer is live with matching identity and contract "
                    "coordinate, but the directly observed monthly fee changed."
                )

            return ExactOfferLifecycleResult(
                status=status,
                offer_key=historical.offer_key,
                provider=historical.provider,
                checked_url=historical.url,
                final_url=final_url,
                http_status=http_status,
                checked_at=checked_at,
                historical_observed_at=historical.observed_at,
                historical_monthly_fee=historical.monthly_fee,
                live_monthly_fee=live.monthly_fee,
                monthly_fee_delta_huf=delta,
                historical_identity=historical_identity,
                live_identity=live_identity,
                historical_contract=historical_contract,
                live_contract=live_contract,
                diagnostic=diagnostic,
            )

        finally:
            page.close()

    def _unresolved(
        self,
        historical,
        *,
        checked_at,
        final_url,
        http_status,
        diagnostic,
    ):
        return ExactOfferLifecycleResult(
            status=LIFECYCLE_UNRESOLVED,
            offer_key=historical.offer_key,
            provider=historical.provider,
            checked_url=historical.url,
            final_url=final_url,
            http_status=http_status,
            checked_at=checked_at,
            historical_observed_at=historical.observed_at,
            historical_monthly_fee=historical.monthly_fee,
            live_monthly_fee=None,
            monthly_fee_delta_huf=None,
            historical_identity=self._historical_identity(
                historical
            ),
            live_identity=None,
            historical_contract=self._historical_contract(
                historical
            ),
            live_contract=None,
            diagnostic=diagnostic,
        )

    def _historical_identity(
        self,
        historical,
    ) -> dict:
        return self.identity_builder(
            historical
        )

    @staticmethod
    def _historical_contract(
        historical,
    ) -> dict:
        return {
            "duration": historical.duration,
            "mileage": historical.mileage,
        }

    @staticmethod
    def _price_delta(
        historical_fee,
        live_fee,
    ):
        if (
            historical_fee is None
            or live_fee is None
        ):
            return None

        return (
            live_fee
            - historical_fee
        )

    @staticmethod
    def _live_from_loaded(
        loaded,
    ) -> LiveOfferObservation:

        # EvidenceAwareCompositeOffer
        if hasattr(
            loaded,
            "composite",
        ):
            offer = loaded.composite.offer

        # CompositeOffer
        elif hasattr(
            loaded,
            "offer",
        ):
            offer = loaded.offer

        # Offer-like object
        else:
            offer = loaded

        return LiveOfferObservation(
            provider=getattr(
                offer,
                "provider",
                "",
            ),
            brand=getattr(
                offer,
                "brand",
                None,
            ),
            model=getattr(
                offer,
                "model",
                None,
            ),
            trim=getattr(
                offer,
                "trim",
                None,
            ),
            fuel_type=getattr(
                offer,
                "fuel_type",
                None,
            ),
            monthly_fee=getattr(
                offer,
                "monthly_fee",
                None,
            ),
            duration=getattr(
                offer,
                "duration",
                None,
            ),
            mileage=getattr(
                offer,
                "mileage",
                None,
            ),
            url=getattr(
                offer,
                "url",
                "",
            ),
        )

    @staticmethod
    def _default_identity(
        offer,
    ) -> dict:
        """
        Conservative exact identity.
        No fuzzy matching and no trim inference.
        """

        def norm(value):
            return " ".join(
                str(value or "")
                .casefold()
                .replace("–", "-")
                .split()
            )

        return {
            "brand": norm(
                getattr(
                    offer,
                    "brand",
                    None,
                )
            ),
            "model": norm(
                getattr(
                    offer,
                    "model",
                    None,
                )
            ),
            "trim": norm(
                getattr(
                    offer,
                    "trim",
                    None,
                )
            ),
            "fuel_type": norm(
                getattr(
                    offer,
                    "fuel_type",
                    None,
                )
            ),
        }

    @staticmethod
    def _now():
        return datetime.now(
            timezone.utc
        ).isoformat()
