from datetime import datetime

from models.offer import Offer
from models.vehicle_specification import (
    EVIDENCE_OBSERVED,
    VehicleEvidence,
    VehicleSpecification,
)
from models.composite_offer import CompositeOffer

from scrapers.arval.parser import ArvalParser
from scrapers.arval.fuel_parser import (
    ArvalFuelParser,
)
from scrapers.arval.offer_details_parser import (
    ArvalOfferDetailsParser,
)
from scrapers.arval.vehicle_identity_parser import (
    ArvalVehicleIdentityParser,
)


class ArvalCompositeOfferBuilder:
    """
    Arval CompositeOffer Builder V2.

    Uses the hardened ArvalFuelParser for fuel identity.
    """

    def __init__(self):
        self.base = ArvalParser()
        self.fuel_parser = ArvalFuelParser()
        self.details = ArvalOfferDetailsParser()
        self.identity = ArvalVehicleIdentityParser()

    def build(self, page) -> CompositeOffer:

        title = self.base.parse_title(page)

        brand = self.identity.parse_brand(
            page,
            title,
        )

        model = self.identity.parse_model_name(
            page,
            title,
        )

        trim = self.identity.parse_trim(
            page,
            title,
            brand,
            model,
        )

        fuel = self.fuel_parser.parse(
            page
        )

        fee = self.base.parse_monthly_fee(
            page
        )

        duration = self.base.parse_duration(
            page
        )

        mileage = self.base.parse_mileage(
            page
        )

        services = self.details.parse_services(
            page
        )

        financial = (
            self.details
            .build_financial_conditions(
                page,
                fee,
            )
        )

        offer = Offer(
            provider="Arval",
            brand=brand,
            model=model,
            trim=trim,
            fuel_type=fuel,
            monthly_fee=fee,
            duration=duration,
            mileage=mileage,
            url=page.url,
            scraped_at=datetime.now(),
        )

        vehicle = VehicleSpecification(
            brand=brand,
            model=model,
            trim=trim,
            fuel_type=fuel,
            brand_evidence=self._ve(
                page,
                brand,
            ),
            model_evidence=self._ve(
                page,
                model,
            ),
            trim_evidence=self._ve(
                page,
                trim,
            ),
            fuel_evidence=self._ve(
                page,
                fuel,
            ),
            standard_equipment=[],
            optional_equipment=[],
        )

        return CompositeOffer(
            offer=offer,
            vehicle=vehicle,
            services=services,
            financial=financial,
        )

    @staticmethod
    def _ve(
        page,
        text,
    ):
        return VehicleEvidence(
            status=EVIDENCE_OBSERVED,
            source_url=page.url,
            source_text=text,
        )
