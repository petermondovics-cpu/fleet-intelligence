import re
from dataclasses import dataclass
from typing import List, Optional

from playwright.sync_api import Page

from models.financial_conditions import (
    DownPayment,
    FinancialConditions,
    FinancialEvidence,
    ServiceItem,
    ServicePackage,
    EVIDENCE_OBSERVED,
    EVIDENCE_UNKNOWN,
)


@dataclass(frozen=True)
class CustomQuoteCapabilities:
    """
    Ayvens quote-request controls.

    IMPORTANT:
    These controls are metadata only.
    They MUST NOT generate Offer variants and MUST NOT be used
    as contract-pricing evidence.
    """

    duration_min: Optional[int]
    duration_max: Optional[int]
    duration_step: Optional[int]

    mileage_min: Optional[int]
    mileage_max: Optional[int]
    mileage_step: Optional[int]


class AyvensOfferDetailsParser:
    """
    Ayvens Offer Details Parser V1.

    Scope:
    - advertised services
    - advertised down-payment control state
    - quote-request slider capabilities

    Explicit architecture rule:
    slider values are NOT priced contract variants.
    """

    SERVICE_MAP = {
        "Teljes körű karbantartás": (
            "MAINTENANCE",
            "Teljes körű karbantartás",
        ),
        "Téli-, nyári gumiabroncs": (
            "TYRES",
            "Téli-, nyári gumiabroncs",
        ),
        "Assistance szolgáltatás": (
            "MOBILITY",
            "Assistance szolgáltatás",
        ),
        "MyAyvens online ügyintézési rendszer": (
            "ADMINISTRATION",
            "MyAyvens online ügyintézési rendszer",
        ),
        "Vonatkozó adók": (
            "TAX",
            "Vonatkozó adók",
        ),
        "Biztosítási csomag": (
            "INSURANCE",
            "Biztosítási csomag",
        ),
    }

    # ============================================================
    # SERVICES
    # ============================================================

    def parse_services(
        self,
        page: Page,
    ) -> ServicePackage:

        items: List[ServiceItem] = []

        service_block = self._find_service_block(
            page
        )

        if service_block is None:
            return ServicePackage()

        for visible_text, (
            category,
            canonical_name,
        ) in self.SERVICE_MAP.items():

            locator = service_block.get_by_text(
                visible_text,
                exact=True,
            )

            if locator.count() == 0:
                continue

            items.append(
                ServiceItem(
                    name=canonical_name,
                    category=category,
                    included=True,
                    evidence=FinancialEvidence(
                        status=EVIDENCE_OBSERVED,
                        source_url=page.url,
                        source_text=visible_text,
                    ),
                )
            )

        return ServicePackage(
            items=items
        )

    def _find_service_block(
        self,
        page: Page,
    ):

        heading = page.get_by_text(
            "Havidíjban foglalt szolgáltatások",
            exact=True,
        )

        if heading.count() == 0:
            return None

        candidate = heading.first

        # Walk upward until the known service texts appear together.
        for _ in range(6):

            parent = candidate.locator(
                "xpath=.."
            )

            if parent.count() == 0:
                break

            try:
                text = (
                    parent.inner_text()
                    .strip()
                )
            except Exception:
                break

            if (
                "Teljes körű karbantartás" in text
                and "Biztosítási csomag" in text
            ):
                return parent

            candidate = parent

        return None

    # ============================================================
    # DOWN PAYMENT
    # ============================================================

    def parse_down_payment(
        self,
        page: Page,
    ) -> DownPayment:

        label = page.get_by_text(
            "Induló befizetés",
            exact=True,
        )

        if label.count() == 0:

            return DownPayment(
                percent=None,
                amount=None,
                status=EVIDENCE_UNKNOWN,
                evidence=FinancialEvidence(
                    status=EVIDENCE_UNKNOWN,
                ),
            )

        container = label.first.locator(
            "xpath=.."
        )

        switch = container.locator(
            "input[role='switch']"
        )

        # Fallback: the switch may be one level higher.
        if switch.count() == 0:
            switch = (
                container
                .locator("xpath=..")
                .locator(
                    "input[role='switch']"
                )
            )

        if switch.count() == 0:

            return DownPayment(
                percent=None,
                amount=None,
                status=EVIDENCE_UNKNOWN,
                evidence=FinancialEvidence(
                    status=EVIDENCE_UNKNOWN,
                ),
            )

        checked = (
            switch.first.is_checked()
        )

        # IMPORTANT:
        # Checked only proves that an upfront-payment mode is active.
        # It does NOT prove a percentage or HUF amount.
        #
        # V1 therefore deliberately keeps percent/amount UNKNOWN.
        if checked:

            return DownPayment(
                percent=None,
                amount=None,
                status=EVIDENCE_UNKNOWN,
                evidence=FinancialEvidence(
                    status=EVIDENCE_UNKNOWN,
                ),
            )

        # Disabled/off also does not prove "0% down payment":
        # it only proves the UI switch is off.
        return DownPayment(
            percent=None,
            amount=None,
            status=EVIDENCE_UNKNOWN,
            evidence=FinancialEvidence(
                status=EVIDENCE_UNKNOWN,
            ),
        )

    # ============================================================
    # QUOTE CAPABILITIES
    # ============================================================

    def parse_quote_capabilities(
        self,
        page: Page,
    ) -> CustomQuoteCapabilities:

        duration = self._range_by_label(
            page,
            "Futamidő",
        )

        mileage = self._range_by_label(
            page,
            "Futásteljesítmény",
        )

        return CustomQuoteCapabilities(
            duration_min=self._int_attr(
                duration,
                "min",
            ),
            duration_max=self._int_attr(
                duration,
                "max",
            ),
            duration_step=self._int_attr(
                duration,
                "step",
            ),
            mileage_min=self._int_attr(
                mileage,
                "min",
            ),
            mileage_max=self._int_attr(
                mileage,
                "max",
            ),
            mileage_step=self._int_attr(
                mileage,
                "step",
            ),
        )

    def _range_by_label(
        self,
        page: Page,
        label_text: str,
    ):

        label = page.get_by_text(
            label_text,
            exact=True,
        )

        if label.count() == 0:
            return None

        current = label.first

        for _ in range(5):

            parent = current.locator(
                "xpath=.."
            )

            if parent.count() == 0:
                break

            range_input = parent.locator(
                "input[type='range']"
            )

            if range_input.count() > 0:
                return range_input.first

            current = parent

        return None

    @staticmethod
    def _int_attr(
        locator,
        attribute: str,
    ) -> Optional[int]:

        if locator is None:
            return None

        try:
            value = locator.get_attribute(
                attribute
            )
        except Exception:
            return None

        if value is None:
            return None

        try:
            return int(value)
        except ValueError:
            return None

    # ============================================================
    # FINANCIAL CONDITIONS
    # ============================================================

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
            monthly_fee_evidence=(
                FinancialEvidence(
                    status=EVIDENCE_OBSERVED,
                    source_url=page.url,
                    source_text=(
                        f"{monthly_fee} Ft/hó"
                    ),
                )
            ),
        )
