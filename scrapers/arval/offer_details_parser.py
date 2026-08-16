from typing import List

from playwright.sync_api import Page

from models.financial_conditions import (
    EVIDENCE_OBSERVED,
    EVIDENCE_UNKNOWN,
    DownPayment,
    FinancialConditions,
    FinancialEvidence,
    ServiceItem,
    ServicePackage,
)


class ArvalOfferDetailsParser:
    """
    Arval Offer Details Parser V1.

    Scope:
    - 6 included service items
    - safe financial conditions
    - NO equipment parsing here

    Provider rule:
    Arval detail pages do not publish standard/optional equipment lists.
    Equipment therefore remains NOT_PUBLISHED at the provider layer.
    """

    SERVICE_MAP = {
        "Biztosítás és káresemény-kezelés": (
            "INSURANCE",
            "Biztosítás és káresemény-kezelés",
        ),
        "Finanszírozás": (
            "FINANCING",
            "Finanszírozás",
        ),
        "Gumiabroncs kezelés": (
            "TYRES",
            "Gumiabroncs kezelés",
        ),
        "Karbantartás és javítás": (
            "MAINTENANCE",
            "Karbantartás és javítás",
        ),
        "Közúti segítségnyújtás": (
            "MOBILITY",
            "Közúti segítségnyújtás",
        ),
        "My Arval": (
            "ADMINISTRATION",
            "My Arval",
        ),
    }

    def parse_services(
        self,
        page: Page,
    ) -> ServicePackage:

        items: List[ServiceItem] = []

        for visible_text, (
            category,
            canonical_name,
        ) in self.SERVICE_MAP.items():

            locator = page.locator(
                "span.service-title"
            ).filter(
                has_text=visible_text
            )

            if locator.count() == 0:
                continue

            source_text = (
                locator.first
                .inner_text()
                .strip()
            )

            items.append(
                ServiceItem(
                    name=canonical_name,
                    category=category,
                    included=True,
                    evidence=FinancialEvidence(
                        status=EVIDENCE_OBSERVED,
                        source_url=page.url,
                        source_text=source_text,
                    ),
                )
            )

        return ServicePackage(
            items=items
        )

    def parse_down_payment(
        self,
        page: Page,
    ) -> DownPayment:
        """
        Arval V1:
        no explicit down-payment value is assumed unless an actual
        percentage/amount is observed in the offer page.
        """

        body = (
            page.locator("body")
            .inner_text()
        )

        # Conservative V1: we do not infer from generic wording.
        # A dedicated explicit parser can be added later if Arval
        # starts publishing a percentage or HUF amount.
        return DownPayment(
            percent=None,
            amount=None,
            status=EVIDENCE_UNKNOWN,
            evidence=FinancialEvidence(
                status=EVIDENCE_UNKNOWN,
            ),
        )

    def build_financial_conditions(
        self,
        page: Page,
        monthly_fee: int,
    ) -> FinancialConditions:

        return FinancialConditions(
            monthly_fee=monthly_fee,
            down_payment=self.parse_down_payment(
                page
            ),
            monthly_fee_evidence=FinancialEvidence(
                status=EVIDENCE_OBSERVED,
                source_url=page.url,
                source_text=(
                    f"{monthly_fee} Ft/hó"
                ),
            ),
        )
