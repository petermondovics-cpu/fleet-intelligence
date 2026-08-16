from dataclasses import dataclass
from typing import Optional

from models.offer import Offer
from models.vehicle_specification import (
    VehicleSpecification,
)
from models.financial_conditions import (
    ServicePackage,
    FinancialConditions,
)


@dataclass(frozen=True)
class CompositeOffer:
    """
    Composite Offer V2.

    Keeps the existing Offer object as the canonical legacy/base
    commercial record and attaches the richer V1 specification layers.

    No price normalization or comparability calculation is performed
    here. This class is a data-integrity boundary only.
    """

    offer: Offer
    vehicle: VehicleSpecification
    services: ServicePackage
    financial: FinancialConditions

    def __post_init__(self):

        if self.offer.provider.strip() == "":
            raise ValueError(
                "Offer provider cannot be empty."
            )

        if (
            self.financial.monthly_fee is not None
            and self.offer.monthly_fee != self.financial.monthly_fee
        ):
            raise ValueError(
                "Financial monthly fee does not match "
                "Offer.monthly_fee."
            )

        if (
            self.vehicle.brand is not None
            and self.offer.brand.strip()
            and self.vehicle.brand.strip().lower()
            != self.offer.brand.strip().lower()
        ):
            raise ValueError(
                "Vehicle brand does not match Offer.brand."
            )

        if (
            self.vehicle.model is not None
            and self.offer.model.strip()
            and self.vehicle.model.strip().lower()
            not in self.offer.model.strip().lower()
            and self.offer.model.strip().lower()
            not in self.vehicle.model.strip().lower()
        ):
            raise ValueError(
                "Vehicle model does not match Offer.model."
            )

        if (
            self.vehicle.fuel_type is not None
            and self.offer.fuel_type.strip()
            and self.vehicle.fuel_type.strip().lower()
            != self.offer.fuel_type.strip().lower()
        ):
            raise ValueError(
                "Vehicle fuel type does not match Offer."
            )

    @property
    def provider(self) -> str:
        return self.offer.provider

    @property
    def monthly_fee(self) -> int:
        return self.offer.monthly_fee

    @property
    def duration(self) -> int:
        return self.offer.duration

    @property
    def mileage(self) -> int:
        return self.offer.mileage

    @property
    def advertised_price(self) -> int:
        return self.offer.monthly_fee

    @property
    def down_payment_known(self) -> bool:
        return (
            self.financial.down_payment.status
            != "UNKNOWN"
        )

    @property
    def included_service_count(self) -> int:
        return len(
            self.services.included()
        )

    @property
    def optional_equipment_count(self) -> int:
        return (
            self.vehicle.optional_equipment_count
        )

    @property
    def standard_equipment_count(self) -> int:
        return (
            self.vehicle.standard_equipment_count
        )

    def has_service(
        self,
        category: str,
        name: Optional[str] = None,
    ) -> Optional[bool]:
        return self.services.has_service(
            category,
            name,
        )
