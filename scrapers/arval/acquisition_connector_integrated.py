from comparison.arval_exact_offer_service_evidence_resolver import (
    ArvalExactOfferServiceEvidenceResolver,
)
from scrapers.arval.acquisition_connector import (
    ArvalAcquisitionConnector,
)


class ArvalServiceIntegratedAcquisitionConnector(
    ArvalAcquisitionConnector
):
    """
    Arval Acquisition Connector + Exact-Offer Service Integration V1.

    Service acquisition order:
    1. exact-offer structured service accordion;
    2. existing ArvalAcquisitionConnector.service_discovery fallback.

    Safety:
    - only resolver status VALIDATED is promoted;
    - every promoted assertion has applicability_scope EXACT_OFFER;
    - absence never becomes included=False;
    - generic fallback behavior remains delegated to the existing connector.
    """

    def __init__(
        self,
        browser,
        canonical_key_builder=None,
    ):
        super().__init__(
            browser,
            canonical_key_builder=canonical_key_builder,
        )

        self.exact_offer_service_resolver = (
            ArvalExactOfferServiceEvidenceResolver(
                browser
            )
        )

    def service_discovery(
        self,
        task,
    ):
        current_url = getattr(
            task,
            "current_url",
            None,
        )

        if current_url:
            try:
                result = (
                    self.exact_offer_service_resolver
                    .resolve(
                        current_url
                    )
                )

                if (
                    result.status
                    == "VALIDATED"
                    and result.evidence
                ):
                    assertions = tuple(
                        {
                            "code": item.code,
                            "included": True,
                            "source_text": item.source_text,
                        }
                        for item in result.evidence
                        if (
                            item.applicability_scope
                            == "EXACT_OFFER"
                        )
                    )

                    if assertions:
                        return {
                            "source_type": "PROVIDER_OFFER_PAGE",
                            "source_url": current_url,
                            "source_text": " | ".join(
                                item["source_text"]
                                for item in assertions
                            ),
                            "services": assertions,
                            "applicability_scope": "EXACT_OFFER",
                            "evidence_method": (
                                "STRUCTURED_SERVICE_ACCORDION_DOM"
                            ),
                        }

            except Exception:
                # Exact-offer acquisition failure must not destroy the
                # pre-existing generic provider fallback path.
                pass

        return super().service_discovery(
            task
        )
