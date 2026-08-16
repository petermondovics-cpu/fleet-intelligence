from datetime import datetime

from models.offer import Offer
from models.vehicle_specification import (
    EVIDENCE_OBSERVED,
    VehicleEvidence,
    VehicleSpecification,
)
from models.composite_offer import CompositeOffer

from scrapers.ayvens.parser import AyvensParser
from scrapers.ayvens.offer_details_parser import (
    AyvensOfferDetailsParser,
)
from scrapers.ayvens.equipment_parser import (
    AyvensEquipmentParser,
    EQUIPMENT_PARSING_UNRESOLVED,
)
from scrapers.ayvens.vehicle_identity_parser import (
    AyvensVehicleIdentityParser,
)


class AyvensCompositeOfferBuilder:
    """
    Builds one CompositeOffer from the advertised Ayvens contract.

    IMPORTANT:
    Quote-request sliders are metadata only.
    They must never create priced Offer variants.
    """

    def __init__(self):
        self.base = AyvensParser()
        self.details = AyvensOfferDetailsParser()
        self.equipment = AyvensEquipmentParser()
        self.identity = AyvensVehicleIdentityParser()

    def build(self, page) -> CompositeOffer:

        brand = self.identity.parse_brand(page)
        model = self.identity.parse_model_name(page)
        trim = self.identity.parse_trim(page)

        fuel = self.base.parse_fuel_type(page)
        fee = self.base.parse_monthly_fee(page)
        duration = self.base.parse_duration(page)
        mileage = self.base.parse_mileage(page)

        standard = self.equipment.parse_standard_equipment(page)
        optional = self.equipment.parse_optional_equipment(page)

        if standard.status == EQUIPMENT_PARSING_UNRESOLVED:
            raise ValueError(
                "Ayvens standard equipment parsing unresolved; "
                "CompositeOffer creation blocked."
            )

        if optional.status == EQUIPMENT_PARSING_UNRESOLVED:
            raise ValueError(
                "Ayvens optional equipment parsing unresolved; "
                "CompositeOffer creation blocked."
            )

        services = self.details.parse_services(page)

        financial = self.details.build_financial_conditions(
            page,
            fee,
        )

        offer = Offer(
            provider="Ayvens",
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
            brand_evidence=self._ve(page, brand),
            model_evidence=self._ve(page, model),
            trim_evidence=self._ve(page, trim),
            fuel_evidence=self._ve(page, fuel),
            standard_equipment=standard.items,
            optional_equipment=optional.items,
        )

        return CompositeOffer(
            offer=offer,
            vehicle=vehicle,
            services=services,
            financial=financial,
        )

    def parse_quote_capabilities(self, page):
        return self.details.parse_quote_capabilities(page)

    @staticmethod
    def _ve(page, text):
        return VehicleEvidence(
            status=EVIDENCE_OBSERVED,
            source_url=page.url,
            source_text=text,
        )
