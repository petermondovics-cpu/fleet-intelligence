import re
from dataclasses import dataclass
from typing import Optional, Tuple
from urllib.parse import urljoin, urlsplit

from models.financial_conditions import EVIDENCE_OBSERVED
from scrapers.arval.offer_route_resolver import (
    ROUTE_LIVE,
    ArvalOfferRouteResolver,
)


FINANCIAL_OBSERVED = "OBSERVED"
FINANCIAL_REVIEWED_NOT_PUBLISHED = "REVIEWED_NOT_PUBLISHED"
FINANCIAL_UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class FinancialEvidenceReview:
    provider: str
    status: str
    source_url: Optional[str]
    reviewed_surfaces: Tuple[str, ...]
    down_payment_percent: Optional[float]
    down_payment_amount_huf: Optional[int]
    diagnostic: str


class FinancialEvidenceProvenanceResolverV1_1:
    """
    Financial Evidence Provenance Resolver V1.1.

    V1.1 change
    -----------
    Arval quote-flow traversal no longer depends only on a successful DOM click.

    If the exact-offer CTA exposes a provider-owned href, V1.1:
    1. validates the href stays on arval.hu;
    2. follows the href directly with page.goto();
    3. verifies a quote-flow page was actually reached;
    4. scans that page for explicit financial evidence;
    5. never submits the form.

    Safety
    ------
    - REVIEWED_NOT_PUBLISHED remains distinct from OBSERVED.
    - REVIEWED_NOT_PUBLISHED never means 0%.
    - absence never becomes evidence.
    - only provider-owned Arval navigation is followed.
    - no form is submitted.
    """

    ARVAL_HOSTS = {
        "arval.hu",
        "www.arval.hu",
    }

    ZERO_PATTERNS = (
        re.compile(
            r"(?:0\s*%\s*(?:önerő|onero)|"
            r"(?:önerő|onero).{0,40}?0\s*%|"
            r"(?:önerő|onero)\s*nélkül|"
            r"(?:önerő|onero)\s*nelkul|"
            r"kezdő\s*befizetés\s*nélkül|"
            r"kezdo\s*befizetes\s*nelkul)",
            re.IGNORECASE | re.DOTALL,
        ),
    )

    PERCENT_PATTERNS = (
        re.compile(
            r"(?:önerő|onero|kezdő\s*befizetés|kezdo\s*befizetes|"
            r"első\s*befizetés|elso\s*befizetes)"
            r".{0,100}?(\d{1,3}(?:[.,]\d+)?)\s*%",
            re.IGNORECASE | re.DOTALL,
        ),
        re.compile(
            r"(\d{1,3}(?:[.,]\d+)?)\s*%"
            r".{0,100}?(?:önerő|onero|kezdő\s*befizetés|"
            r"kezdo\s*befizetes|első\s*befizetés|elso\s*befizetes)",
            re.IGNORECASE | re.DOTALL,
        ),
    )

    AMOUNT_PATTERNS = (
        re.compile(
            r"(?:önerő|onero|kezdő\s*befizetés|kezdo\s*befizetes|"
            r"első\s*befizetés|elso\s*befizetes)"
            r".{0,120}?(\d[\d\s.,]{2,})\s*(?:Ft|HUF)",
            re.IGNORECASE | re.DOTALL,
        ),
    )

    def __init__(self, browser):
        self.browser = browser

    def resolve(
        self,
        provider: str,
        url: str,
        financial,
    ) -> FinancialEvidenceReview:

        provider_name = str(provider or "")
        down_payment = getattr(
            financial,
            "down_payment",
            None,
        )

        if (
            down_payment is not None
            and getattr(
                down_payment,
                "status",
                None,
            ) == EVIDENCE_OBSERVED
        ):
            return FinancialEvidenceReview(
                provider=provider_name,
                status=FINANCIAL_OBSERVED,
                source_url=(
                    getattr(
                        getattr(
                            down_payment,
                            "evidence",
                            None,
                        ),
                        "source_url",
                        None,
                    )
                    or url
                ),
                reviewed_surfaces=(
                    "ENRICHED_PROVIDER_EVIDENCE",
                ),
                down_payment_percent=getattr(
                    down_payment,
                    "percent",
                    None,
                ),
                down_payment_amount_huf=getattr(
                    down_payment,
                    "amount",
                    None,
                ),
                diagnostic=(
                    "Explicit provider down-payment evidence is already "
                    "present in the enriched financial comparison view."
                ),
            )

        if provider_name.casefold() != "arval":
            return FinancialEvidenceReview(
                provider=provider_name,
                status=FINANCIAL_UNRESOLVED,
                source_url=url,
                reviewed_surfaces=(),
                down_payment_percent=None,
                down_payment_amount_huf=None,
                diagnostic=(
                    "No explicit down-payment evidence is present and V1.1 "
                    "deep quote-flow review is implemented for Arval only."
                ),
            )

        return self._review_arval(
            url
        )

    def _review_arval(
        self,
        url: str,
    ) -> FinancialEvidenceReview:

        page = self.browser.new_page()
        reviewed = []

        try:
            route = (
                ArvalOfferRouteResolver()
                .resolve(
                    page,
                    url,
                    timeout=60000,
                    settle_ms=1500,
                )
            )

            if (
                route.status != ROUTE_LIVE
                or not route.resolved_url
            ):
                return self._unresolved(
                    url,
                    reviewed,
                    (
                        "Arval exact-offer route could not be validated; "
                        "financial publication state remains unresolved."
                    ),
                )

            reviewed.append(
                "EXACT_OFFER"
            )

            exact_parsed = self._parse(
                self._body(
                    page
                )
            )

            if exact_parsed is not None:
                return self._observed(
                    page.url,
                    reviewed,
                    exact_parsed,
                    (
                        "Explicit down-payment evidence was observed on "
                        "the Arval exact-offer page."
                    ),
                )

            quote_target = (
                self._quote_target(
                    page,
                    route.resolved_url,
                )
            )

            if quote_target is None:
                return FinancialEvidenceReview(
                    provider="Arval",
                    status=FINANCIAL_REVIEWED_NOT_PUBLISHED,
                    source_url=route.resolved_url,
                    reviewed_surfaces=tuple(
                        reviewed
                    ),
                    down_payment_percent=None,
                    down_payment_amount_huf=None,
                    diagnostic=(
                        "Arval exact offer was reviewed and no explicit "
                        "down-payment condition was published. No safe "
                        "provider-owned quote-flow target was exposed."
                    ),
                )

            quote_url = (
                quote_target["url"]
            )

            response = page.goto(
                quote_url,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            page.wait_for_timeout(
                1500
            )

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
                return self._unresolved(
                    route.resolved_url,
                    reviewed,
                    (
                        "Arval quote-flow target was provider-owned but did "
                        f"not return HTTP 2xx. HTTP={status}."
                    ),
                )

            if not self._is_arval_url(
                page.url
            ):
                return self._unresolved(
                    route.resolved_url,
                    reviewed,
                    (
                        "Quote-flow navigation left the Arval domain; "
                        "review was stopped."
                    ),
                )

            if not self._quote_flow_reached(
                page,
                quote_url,
            ):
                return self._unresolved(
                    route.resolved_url,
                    reviewed,
                    (
                        "Provider-owned quote-flow target loaded, but a "
                        "quote-request surface could not be safely verified."
                    ),
                )

            reviewed.append(
                "QUOTE_FLOW"
            )

            quote_parsed = self._parse(
                self._body(
                    page
                )
            )

            if quote_parsed is not None:
                return self._observed(
                    page.url,
                    reviewed,
                    quote_parsed,
                    (
                        "Explicit down-payment evidence was observed on "
                        "the Arval quote-flow page."
                    ),
                )

            return FinancialEvidenceReview(
                provider="Arval",
                status=FINANCIAL_REVIEWED_NOT_PUBLISHED,
                source_url=route.resolved_url,
                reviewed_surfaces=tuple(
                    reviewed
                ),
                down_payment_percent=None,
                down_payment_amount_huf=None,
                diagnostic=(
                    "Arval exact offer and provider-owned quote-flow page "
                    "were reviewed. No explicit down-payment percentage, "
                    "amount, or zero-down statement was published. "
                    "Down payment remains UNKNOWN."
                ),
            )

        except Exception as exc:
            return self._unresolved(
                url,
                reviewed,
                (
                    "Arval financial publication review failed safely: "
                    f"{type(exc).__name__}: {exc}"
                ),
            )

        finally:
            page.close()

    @classmethod
    def _quote_target(
        cls,
        page,
        base_url: str,
    ):
        selectors = (
            "a.offer-tunnel-link",
            "a:has-text('AJÁNLAT KIVÁLASZTÁSA')",
        )

        for selector in selectors:
            locator = page.locator(
                selector
            )

            try:
                count = locator.count()
            except Exception:
                continue

            for index in range(
                count
            ):
                item = locator.nth(
                    index
                )

                try:
                    if not item.is_visible():
                        continue

                    text = (
                        item.inner_text()
                        .strip()
                    )

                    href = (
                        item.get_attribute(
                            "href"
                        )
                    )
                except Exception:
                    continue

                if not href:
                    continue

                folded = (
                    text.casefold()
                )

                if (
                    "ajánlat kiválasztása"
                    not in folded
                    and "ajanlat kivalasztasa"
                    not in folded
                ):
                    continue

                absolute = urljoin(
                    base_url,
                    href,
                )

                if not cls._is_arval_url(
                    absolute
                ):
                    continue

                return {
                    "url": absolute,
                    "href": href,
                    "text": text,
                }

        return None

    @classmethod
    def _quote_flow_reached(
        cls,
        page,
        requested_url: str,
    ) -> bool:

        if not cls._is_arval_url(
            page.url
        ):
            return False

        final_path = (
            urlsplit(
                page.url
            )
            .path
            .casefold()
        )

        requested_path = (
            urlsplit(
                requested_url
            )
            .path
            .casefold()
        )

        # Strongest signal: provider navigated into its quote-request route.
        if (
            "árajánlatkérés" in final_path
            or "%c3%a1raj%c3%a1nlatk%c3%a9r%c3%a9s"
            in final_path
            or "arajanlatkeres" in final_path
        ):
            return True

        # Provider may redirect the /switch endpoint into a form page.
        if (
            final_path != requested_path
            and page.locator("form").count() > 0
        ):
            return True

        # A form on the resolved provider-owned target is acceptable as a
        # quote-flow surface, provided navigation itself succeeded.
        try:
            return page.locator(
                "form"
            ).count() > 0
        except Exception:
            return False

    @classmethod
    def _parse(
        cls,
        text,
    ):
        normalized = re.sub(
            r"\s+",
            " ",
            text or "",
        )

        for pattern in cls.ZERO_PATTERNS:
            if pattern.search(
                normalized
            ):
                return (
                    0.0,
                    None,
                )

        for pattern in cls.PERCENT_PATTERNS:
            match = pattern.search(
                normalized
            )

            if match:
                return (
                    float(
                        match.group(1)
                        .replace(
                            ",",
                            ".",
                        )
                    ),
                    None,
                )

        for pattern in cls.AMOUNT_PATTERNS:
            match = pattern.search(
                normalized
            )

            if match:
                digits = re.sub(
                    r"\D",
                    "",
                    match.group(1),
                )

                if digits:
                    return (
                        None,
                        int(
                            digits
                        ),
                    )

        return None

    @classmethod
    def _is_arval_url(
        cls,
        url: str,
    ) -> bool:

        try:
            host = (
                urlsplit(
                    url
                )
                .hostname
                or ""
            ).casefold()
        except Exception:
            return False

        return host in cls.ARVAL_HOSTS

    @staticmethod
    def _body(
        page,
    ):
        try:
            return (
                page.locator(
                    "body"
                )
                .inner_text(
                    timeout=5000
                )
            )
        except Exception:
            return ""

    @staticmethod
    def _observed(
        source_url,
        reviewed,
        parsed,
        diagnostic,
    ):
        percent, amount = parsed

        return FinancialEvidenceReview(
            provider="Arval",
            status=FINANCIAL_OBSERVED,
            source_url=source_url,
            reviewed_surfaces=tuple(
                reviewed
            ),
            down_payment_percent=percent,
            down_payment_amount_huf=amount,
            diagnostic=diagnostic,
        )

    @staticmethod
    def _unresolved(
        source_url,
        reviewed,
        diagnostic,
    ):
        return FinancialEvidenceReview(
            provider="Arval",
            status=FINANCIAL_UNRESOLVED,
            source_url=source_url,
            reviewed_surfaces=tuple(
                reviewed
            ),
            down_payment_percent=None,
            down_payment_amount_huf=None,
            diagnostic=diagnostic,
        )


def _quote_target_from_parts_for_test(
    self,
    base_url,
    href,
    text,
):
    folded = (
        text or ""
    ).casefold()

    if (
        "ajánlat kiválasztása"
        not in folded
        and "ajanlat kivalasztasa"
        not in folded
    ):
        return None

    absolute = urljoin(
        base_url,
        href,
    )

    if not self._is_arval_url(
        absolute
    ):
        return None

    return {
        "url": absolute,
        "href": href,
        "text": text,
    }


FinancialEvidenceProvenanceResolverV1_1._quote_target_from_parts_for_test = (
    _quote_target_from_parts_for_test
)
