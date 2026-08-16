from dataclasses import dataclass, field
from typing import List, Optional


EVIDENCE_OBSERVED = "OBSERVED"
EVIDENCE_INFERRED = "INFERRED"
EVIDENCE_UNKNOWN = "UNKNOWN"

EVIDENCE_STATUSES = {
    EVIDENCE_OBSERVED,
    EVIDENCE_INFERRED,
    EVIDENCE_UNKNOWN,
}


@dataclass(frozen=True)
class FinancialEvidence:
    status: str
    source_url: str = ""
    source_text: str = ""

    def __post_init__(self):
        if self.status not in EVIDENCE_STATUSES:
            raise ValueError(
                f"Invalid evidence status: {self.status}"
            )

        if self.status == EVIDENCE_UNKNOWN:
            if self.source_url or self.source_text:
                raise ValueError(
                    "UNKNOWN evidence cannot contain source data."
                )


@dataclass(frozen=True)
class ServiceItem:
    """
    One service included/excluded in a leasing package.

    included:
        True  = explicitly included
        False = explicitly excluded
        None  = not established

    UNKNOWN is deliberately different from False.
    """

    name: str
    category: str
    included: Optional[bool]
    evidence: FinancialEvidence

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Service name cannot be empty.")

        if not self.category.strip():
            raise ValueError("Service category cannot be empty.")

        if (
            self.evidence.status == EVIDENCE_UNKNOWN
            and self.included is not None
        ):
            raise ValueError(
                "UNKNOWN service evidence cannot assert "
                "included/excluded status."
            )


@dataclass(frozen=True)
class ServicePackage:
    """
    Structured service package V1.

    Categories are intentionally strings in V1 so that provider-specific
    services do not get lost. A later taxonomy can normalize categories.
    """

    items: List[ServiceItem] = field(
        default_factory=list
    )

    def included(self) -> List[ServiceItem]:
        return [
            item
            for item in self.items
            if item.included is True
        ]

    def excluded(self) -> List[ServiceItem]:
        return [
            item
            for item in self.items
            if item.included is False
        ]

    def unknown(self) -> List[ServiceItem]:
        return [
            item
            for item in self.items
            if item.included is None
        ]

    def has_service(
        self,
        category: str,
        name: Optional[str] = None,
    ) -> Optional[bool]:

        matches = [
            item
            for item in self.items
            if item.category == category
            and (
                name is None
                or item.name == name
            )
        ]

        if not matches:
            return None

        if any(
            item.included is True
            for item in matches
        ):
            return True

        if all(
            item.included is False
            for item in matches
        ):
            return False

        return None


@dataclass(frozen=True)
class DownPayment:
    """
    Upfront/down-payment information.

    The percentage is an observed fact only when supported by evidence.
    A benchmark default such as 20% must NOT be stored here as observed data.

    percent:
        Actual observed/inferred percentage, or None.

    amount:
        Actual observed/inferred amount in HUF, or None.

    status:
        OBSERVED / INFERRED / UNKNOWN.
    """

    percent: Optional[float]
    amount: Optional[int]
    status: str
    evidence: FinancialEvidence

    def __post_init__(self):

        if self.status not in EVIDENCE_STATUSES:
            raise ValueError(
                f"Invalid down-payment status: {self.status}"
            )

        if self.status == EVIDENCE_UNKNOWN:
            if (
                self.percent is not None
                or self.amount is not None
            ):
                raise ValueError(
                    "UNKNOWN down payment cannot contain "
                    "an asserted percent or amount."
                )

        if self.percent is not None:
            if (
                self.percent < 0
                or self.percent > 100
            ):
                raise ValueError(
                    "Down-payment percent must be "
                    "between 0 and 100."
                )

        if self.amount is not None:
            if self.amount < 0:
                raise ValueError(
                    "Down-payment amount cannot be negative."
                )

        if (
            self.status == EVIDENCE_OBSERVED
            and self.percent is None
            and self.amount is None
        ):
            raise ValueError(
                "OBSERVED down payment must contain "
                "a percent or amount."
            )


@dataclass(frozen=True)
class FinancialConditions:
    """
    Financial conditions V1.

    monthly_fee is the advertised monthly fee.
    It must not be treated as a comparable/effective price
    until contract and service conditions are normalized.
    """

    monthly_fee: Optional[int]
    down_payment: DownPayment

    other_one_off_fees: Optional[int] = None
    other_recurring_fees: Optional[int] = None

    monthly_fee_evidence: Optional[FinancialEvidence] = None

    def __post_init__(self):

        if self.monthly_fee is not None:
            if self.monthly_fee < 0:
                raise ValueError(
                    "Monthly fee cannot be negative."
                )

        if self.other_one_off_fees is not None:
            if self.other_one_off_fees < 0:
                raise ValueError(
                    "One-off fees cannot be negative."
                )

        if self.other_recurring_fees is not None:
            if self.other_recurring_fees < 0:
                raise ValueError(
                    "Recurring fees cannot be negative."
                )
