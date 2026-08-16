import re
from dataclasses import dataclass
from typing import Optional, Tuple


EXACT_OFFER = "EXACT_OFFER"
OFFER_LINKED_DOCUMENT = "OFFER_LINKED_DOCUMENT"
GENERIC_PROVIDER_DOCUMENTATION = "GENERIC_PROVIDER_DOCUMENTATION"

VALIDATED = "VALIDATED"
UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class SecondaryFinancialEvidence:
    provider: str
    source_url: str
    source_type: str
    applicability_scope: str
    source_text: str
    down_payment_percent: Optional[float]
    down_payment_amount_huf: Optional[int]


@dataclass(frozen=True)
class SecondaryFinancialResolution:
    status: str
    provider: str
    evidence: Tuple[SecondaryFinancialEvidence, ...]
    promotable_evidence: Optional[SecondaryFinancialEvidence]
    diagnostic: str


class ArvalSecondaryFinancialEvidenceResolver:
    """
    Arval Secondary Financial Evidence Resolver V1.

    Searches provider-owned secondary sources reachable from the exact offer
    page and classifies any explicit down-payment wording by applicability.

    Promotion rule:
    - exact-offer or demonstrably offer-linked source: potentially promotable;
    - generic provider documentation: informative only, never promoted to
      exact-offer inclusion/financial state.

    This resolver does not assume that a generic Arval rule applies to the
    advertised vehicle offer.
    """

    FINANCIAL_TERMS = (
        "kezdő befizetés",
        "induló nettó bérleti díj",
        "induló bérleti díj",
        "önerő",
        "előleg",
        "első emelt bérleti díj",
    )

    def __init__(self, browser):
        self.browser = browser

    def resolve(
        self,
        offer_url: str,
    ) -> SecondaryFinancialResolution:

        page = self.browser.new_page()
        evidence = []

        try:
            page.goto(
                offer_url,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(1600)
            self._dismiss(page)

            links = self._collect_provider_links(page)

            for url, label in links:
                item = self._inspect_link(
                    offer_url=offer_url,
                    url=url,
                    label=label,
                )
                if item is not None:
                    evidence.append(item)

            promotable = next(
                (
                    item
                    for item in evidence
                    if item.applicability_scope in {
                        EXACT_OFFER,
                        OFFER_LINKED_DOCUMENT,
                    }
                ),
                None,
            )

            if promotable is not None:
                return SecondaryFinancialResolution(
                    status=VALIDATED,
                    provider="Arval",
                    evidence=tuple(evidence),
                    promotable_evidence=promotable,
                    diagnostic=(
                        "Explicit Arval financial evidence was found in a "
                        "source demonstrably linked to the exact offer."
                    ),
                )

            if evidence:
                return SecondaryFinancialResolution(
                    status=UNRESOLVED,
                    provider="Arval",
                    evidence=tuple(evidence),
                    promotable_evidence=None,
                    diagnostic=(
                        "Explicit Arval financial terminology was found only "
                        "in generic provider documentation. It is not promoted "
                        "to the exact advertised offer."
                    ),
                )

            return SecondaryFinancialResolution(
                status=UNRESOLVED,
                provider="Arval",
                evidence=(),
                promotable_evidence=None,
                diagnostic=(
                    "No explicit down-payment evidence was found in safely "
                    "reachable Arval-owned secondary sources."
                ),
            )

        finally:
            page.close()

    def _collect_provider_links(self, page):
        result = []
        seen = set()

        links = page.locator("a[href]")

        for i in range(links.count()):
            loc = links.nth(i)

            try:
                href = loc.get_attribute("href") or ""
                label = " ".join(loc.inner_text().split())
            except Exception:
                continue

            if not href:
                continue

            if href.startswith("/"):
                href = "https://www.arval.hu" + href

            if not href.startswith("https://www.arval.hu/"):
                continue

            low = (href + " " + label).casefold()

            # Keep likely legal/terms/offer documents. Do not crawl the
            # provider site indiscriminately.
            if not any(
                token in low
                for token in (
                    ".pdf",
                    "aszf",
                    "feltetel",
                    "szerzod",
                    "jogi",
                    "tajekoztato",
                    "ajanlat",
                    "terms",
                    "gtc",
                )
            ):
                continue

            if href in seen:
                continue

            seen.add(href)
            result.append((href, label))

        return tuple(result[:25])

    def _inspect_link(
        self,
        *,
        offer_url: str,
        url: str,
        label: str,
    ) -> Optional[SecondaryFinancialEvidence]:

        # V1 reads HTML-linked secondary pages. PDF links are classified but
        # not parsed through browser text extraction here; they remain for a
        # dedicated PDF/document connector if needed.
        if url.casefold().endswith(".pdf"):
            return None

        page = self.browser.new_page()

        try:
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=45000,
            )
            page.wait_for_timeout(900)

            text = page.locator("body").inner_text()

            parsed = self._parse_explicit_down_payment(text)

            if parsed is None:
                return None

            percent, amount, excerpt = parsed

            scope = self._classify_scope(
                offer_url=offer_url,
                source_url=url,
                label=label,
                text=text,
            )

            return SecondaryFinancialEvidence(
                provider="Arval",
                source_url=url,
                source_type="PROVIDER_SECONDARY_PAGE",
                applicability_scope=scope,
                source_text=excerpt,
                down_payment_percent=percent,
                down_payment_amount_huf=amount,
            )

        except Exception:
            return None

        finally:
            page.close()

    @classmethod
    def _parse_explicit_down_payment(cls, text):

        zero_patterns = (
            r"(?i)\bkezdő\s+befizetés\s+nélkül\b",
            r"(?i)\bönerő\s+nélkül\b",
        )

        for pattern in zero_patterns:
            match = re.search(pattern, text)
            if match:
                return (
                    0.0,
                    0,
                    cls._excerpt(text, match.start(), match.end()),
                )

        percent_patterns = (
            r"(?i)(?:kezdő\s+befizetés|önerő|induló\s+nettó\s+bérleti\s+díj)"
            r"[^0-9%\n]{0,120}(\d{1,3}(?:[.,]\d+)?)\s*%",
            r"(?i)(\d{1,3}(?:[.,]\d+)?)\s*%"
            r"[^.\n]{0,120}(?:kezdő\s+befizetés|önerő|"
            r"induló\s+nettó\s+bérleti\s+díj)",
        )

        for pattern in percent_patterns:
            match = re.search(pattern, text)
            if not match:
                continue

            value = float(
                match.group(1).replace(",", ".")
            )

            if 0 <= value <= 100:
                return (
                    value,
                    None,
                    cls._excerpt(text, match.start(), match.end()),
                )

        amount_patterns = (
            r"(?i)(?:kezdő\s+befizetés|önerő|induló\s+nettó\s+bérleti\s+díj)"
            r"[^0-9\n]{0,120}"
            r"(\d{1,3}(?:[.\s]\d{3})+|\d{4,9})\s*Ft",
        )

        for pattern in amount_patterns:
            match = re.search(pattern, text)
            if match:
                amount = int(
                    re.sub(r"\D", "", match.group(1))
                )
                return (
                    None,
                    amount,
                    cls._excerpt(text, match.start(), match.end()),
                )

        return None

    @staticmethod
    def _classify_scope(
        *,
        offer_url: str,
        source_url: str,
        label: str,
        text: str,
    ) -> str:

        if source_url.rstrip("/") == offer_url.rstrip("/"):
            return EXACT_OFFER

        offer_slug = offer_url.rstrip("/").split("/")[-1].casefold()

        source_blob = (
            source_url + " " + label + " " + text[:2500]
        ).casefold()

        # A secondary page must explicitly carry the exact offer slug/name
        # before V1 considers it offer-linked.
        slug_tokens = [
            token
            for token in re.split(r"[-_/]+", offer_slug)
            if len(token) >= 3
        ]

        strong_tokens = {
            "atto",
            "phev",
            "boost",
        }

        matched = {
            token
            for token in slug_tokens
            if token in source_blob
        }

        if strong_tokens.issubset(matched):
            return OFFER_LINKED_DOCUMENT

        return GENERIC_PROVIDER_DOCUMENTATION

    @staticmethod
    def _excerpt(text, start, end, radius=140):
        lo = max(0, start - radius)
        hi = min(len(text), end + radius)
        return " ".join(text[lo:hi].split())

    @staticmethod
    def _dismiss(page):
        for selector in (
            "#onetrust-reject-all-handler",
            "#onetrust-accept-btn-handler",
            "button:has-text('Összes elfogadása')",
            "button:has-text('Elfogadom')",
            "button:has-text('Elutasítom')",
        ):
            loc = page.locator(selector)
            if loc.count() == 0:
                continue
            try:
                loc.first.click(timeout=1500)
                page.wait_for_timeout(200)
                return
            except Exception:
                pass
