from dataclasses import dataclass
from typing import Optional, Tuple
from urllib.parse import urlsplit, urlunsplit


ROUTE_LIVE = "LIVE"
ROUTE_UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class ArvalOfferRouteResult:
    status: str
    requested_url: str
    resolved_url: Optional[str]
    candidates: Tuple[str, ...]
    diagnostic: str


class ArvalOfferRouteResolver:
    """
    Arval Offer Route Resolver V2.

    Important correction:
    ---------------------
    Repeated final path segments are NOT assumed to be malformed.
    Live evidence shows that many Arval exact-offer routes legitimately use:

        .../<slug>/<slug>

    while some other offers use:

        .../<brand>/<model-slug>

    Therefore route resolution is evidence-based, not shape-based.

    Strategy:
    1. Try the provider-discovered URL exactly as published.
    2. If it contains identical final path segments, also construct a
       collapsed fallback candidate.
    3. A candidate is accepted only when:
       - navigation returns HTTP 2xx; and
       - exact-offer DOM signals become observable.
    4. If both are valid, the provider-discovered URL wins.
    5. No route is rewritten merely because it "looks duplicated".
    """

    def resolve(
        self,
        page,
        url: str,
        timeout: int = 60000,
        settle_ms: int = 1500,
    ) -> ArvalOfferRouteResult:

        candidates = self.candidates(url)
        diagnostics = []

        for candidate in candidates:
            try:
                response = page.goto(
                    candidate,
                    wait_until="domcontentloaded",
                    timeout=timeout,
                )

                page.wait_for_timeout(settle_ms)

                status = (
                    response.status
                    if response is not None
                    else None
                )

                if (
                    status is None
                    or status < 200
                    or status >= 300
                ):
                    diagnostics.append(
                        f"{candidate} -> HTTP {status}"
                    )
                    continue

                if not self._offer_dom_ready(page):
                    diagnostics.append(
                        f"{candidate} -> HTTP {status}, "
                        "but exact-offer DOM signals were not observed."
                    )
                    continue

                return ArvalOfferRouteResult(
                    status=ROUTE_LIVE,
                    requested_url=url,
                    resolved_url=candidate,
                    candidates=candidates,
                    diagnostic=(
                        "Exact Arval offer route validated by HTTP success "
                        "and offer-specific DOM evidence."
                    ),
                )

            except Exception as exc:
                diagnostics.append(
                    f"{candidate} -> {type(exc).__name__}: {exc}"
                )

        return ArvalOfferRouteResult(
            status=ROUTE_UNRESOLVED,
            requested_url=url,
            resolved_url=None,
            candidates=candidates,
            diagnostic=(
                " | ".join(diagnostics)
                if diagnostics
                else "No route candidate could be safely evaluated."
            ),
        )

    @classmethod
    def candidates(
        cls,
        url: str,
    ) -> Tuple[str, ...]:

        candidates = [url]

        collapsed = (
            cls._collapse_identical_final_segment(
                url
            )
        )

        if (
            collapsed
            and collapsed != url
        ):
            candidates.append(
                collapsed
            )

        return tuple(
            dict.fromkeys(
                candidates
            )
        )

    @staticmethod
    def _collapse_identical_final_segment(
        url: str,
    ) -> Optional[str]:

        try:
            parsed = urlsplit(
                url
            )
        except Exception:
            return None

        segments = [
            item
            for item in parsed.path.split("/")
            if item
        ]

        if len(segments) < 2:
            return None

        if (
            segments[-1].casefold()
            != segments[-2].casefold()
        ):
            return None

        collapsed_segments = (
            segments[:-1]
        )

        collapsed_path = (
            "/"
            + "/".join(
                collapsed_segments
            )
        )

        return urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                collapsed_path,
                parsed.query,
                parsed.fragment,
            )
        )

    @staticmethod
    def _offer_dom_ready(
        page,
    ) -> bool:
        """
        Require a compact conjunction of offer-specific signals.

        This avoids accepting a generic Arval 404/template shell merely
        because navigation returned a page.
        """

        try:
            title_count = (
                page.locator(
                    "h1 span"
                )
                .count()
            )

            price_count = (
                page.locator(
                    "span.PricePrimary"
                )
                .count()
            )

            configuration_titles = (
                page.locator(
                    "p.OfferConfigurationTitle"
                )
            )

            duration_count = (
                configuration_titles
                .filter(
                    has_text="Időtartam"
                )
                .count()
            )

            mileage_count = (
                configuration_titles
                .filter(
                    has_text="Futásteljesítmény"
                )
                .count()
            )

            return bool(
                title_count
                and price_count
                and duration_count
                and mileage_count
            )

        except Exception:
            return False
