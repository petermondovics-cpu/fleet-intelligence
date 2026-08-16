from dataclasses import dataclass
from typing import Tuple


VALIDATED = "VALIDATED"
UNRESOLVED = "UNRESOLVED"
EXACT_OFFER = "EXACT_OFFER"


@dataclass(frozen=True)
class ServiceEvidence:
    provider: str
    code: str
    label: str
    source_url: str
    source_text: str
    applicability_scope: str
    source_type: str


@dataclass(frozen=True)
class ServiceEvidenceResolution:
    status: str
    provider: str
    source_url: str
    evidence: Tuple[ServiceEvidence, ...]
    promotable_codes: Tuple[str, ...]
    diagnostic: str


class ArvalExactOfferServiceEvidenceResolver:
    """
    Arval Exact-Offer Service Evidence Resolver V2.

    Evidence is accepted only from:
      #offer-details
        li.accordion-item
          div.accordion-content
            div.service-wrapper
              span.service-title

    This deliberately avoids broad body-text / regex windows.

    Safety:
    - every promoted service must be a concrete service-wrapper in the
      exact offer's accordion content;
    - missing canonical services remain unknown, never excluded;
    - no generic provider page text is promoted.
    """

    TITLE_TO_CODES = {
        "biztosítás és káresemény-kezelés": (
            "INSURANCE",
            "CLAIMS_MANAGEMENT",
        ),
        "finanszírozás": (
            "FINANCING",
        ),
        "gumiabroncs kezelés": (
            "TYRES",
        ),
        "karbantartás és javítás": (
            "MAINTENANCE",
        ),
        "közúti segítségnyújtás": (
            "ROADSIDE_ASSISTANCE",
        ),
        "my arval": (
            "FLEET_PORTAL",
        ),
    }

    def __init__(self, browser):
        self.browser = browser

    def resolve(self, offer_url: str) -> ServiceEvidenceResolution:
        page = self.browser.new_page()

        try:
            page.goto(
                offer_url,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(1600)
            self._dismiss(page)

            details = page.locator("#offer-details")
            if details.count() != 1:
                return self._unresolved(
                    offer_url,
                    "Exact-offer #offer-details container was not found uniquely.",
                )

            items = details.locator("li.accordion-item")
            target = None

            for i in range(items.count()):
                item = items.nth(i)
                title = item.locator("a.accordion-title").first

                try:
                    title_text = " ".join(title.inner_text().split())
                except Exception:
                    continue

                normalized = title_text.casefold()

                if (
                    "szolgáltatás"
                    in normalized
                    and "csomagban"
                    in normalized
                ):
                    target = item
                    break

            if target is None:
                return self._unresolved(
                    offer_url,
                    "Exact-offer service-package accordion was not found.",
                )

            accordion_content = target.locator(
                ":scope > div.accordion-content"
            )

            if accordion_content.count() != 1:
                return self._unresolved(
                    offer_url,
                    "Service-package accordion content was not found uniquely.",
                )

            wrappers = accordion_content.locator(
                "div.service-wrapper"
            )

            evidence = []

            for i in range(wrappers.count()):
                wrapper = wrappers.nth(i)
                title_loc = wrapper.locator(
                    "span.service-title"
                ).first

                try:
                    raw_title = " ".join(
                        title_loc.inner_text().split()
                    )
                except Exception:
                    continue

                if not raw_title:
                    continue

                codes = self.TITLE_TO_CODES.get(
                    raw_title.casefold()
                )

                # Unknown service title is preserved as unclassified.
                # It is not forced into a canonical service code.
                if not codes:
                    continue

                try:
                    wrapper_text = " ".join(
                        wrapper.inner_text().split()
                    )
                except Exception:
                    wrapper_text = raw_title

                for code in codes:
                    evidence.append(
                        ServiceEvidence(
                            provider="Arval",
                            code=code,
                            label=raw_title,
                            source_url=offer_url,
                            source_text=wrapper_text,
                            applicability_scope=EXACT_OFFER,
                            source_type="PROVIDER_OFFER_PAGE_DOM",
                        )
                    )

            promotable_codes = tuple(
                sorted({
                    item.code
                    for item in evidence
                })
            )

            if not promotable_codes:
                return self._unresolved(
                    offer_url,
                    "No canonical service could be mapped from exact-offer "
                    "service-wrapper elements.",
                )

            return ServiceEvidenceResolution(
                status=VALIDATED,
                provider="Arval",
                source_url=offer_url,
                evidence=tuple(evidence),
                promotable_codes=promotable_codes,
                diagnostic=(
                    "Canonical services were directly observed as structured "
                    "service-wrapper elements inside the exact Arval offer's "
                    "service-package accordion."
                ),
            )

        finally:
            page.close()

    @staticmethod
    def _unresolved(
        offer_url: str,
        diagnostic: str,
    ) -> ServiceEvidenceResolution:
        return ServiceEvidenceResolution(
            status=UNRESOLVED,
            provider="Arval",
            source_url=offer_url,
            evidence=(),
            promotable_codes=(),
            diagnostic=diagnostic,
        )

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
