from datetime import datetime

from models.offer import Offer
from models.vehicle_specification import (
    EVIDENCE_OBSERVED,
    VehicleEvidence,
    VehicleSpecification,
)
from models.composite_offer import CompositeOffer
from models.equipment_evidence import (
    EQUIPMENT_NOT_PUBLISHED,
    EQUIPMENT_PARSING_UNRESOLVED,
    EQUIPMENT_PUBLISHED,
    EquipmentEvidenceStatus,
)
from comparison.evidence_aware_comparable import (
    EvidenceAwareCompositeOffer,
)

from scrapers.ayvens.parser import AyvensParser
from scrapers.ayvens.offer_details_parser import (
    AyvensOfferDetailsParser,
)
from scrapers.ayvens.equipment_parser import (
    AyvensEquipmentParser,
    EQUIPMENT_NOT_PUBLISHED as AYVENS_NOT_PUBLISHED,
    EQUIPMENT_PARSING_UNRESOLVED as AYVENS_UNRESOLVED,
    EQUIPMENT_PUBLISHED as AYVENS_PUBLISHED,
)
from scrapers.ayvens.vehicle_identity_parser import (
    AyvensVehicleIdentityParser,
)
from scrapers.ayvens.equipment_publication_resolver import (
    PROVIDER_EQUIPMENT_NOT_PUBLISHED,
    PROVIDER_EQUIPMENT_PUBLISHED,
    AyvensEquipmentPublicationResolver,
)


class AyvensEvidenceAwareBuilder:
    """
    Ayvens Evidence-Aware Builder V3.

    Direct builder matching the current production class shape:
        base / details / equipment / identity / build / parse_quote_capabilities

    V3 resolves an important semantic gap:

    1. The exact Ayvens page contains equipment panels.
    2. The panels may contain no safely extractable equipment items, so the
       DOM parser correctly returns PARSING_UNRESOLVED.
    3. The exact-offer Ayvens API may independently expose
       basic_config=[] and extra_config=[].
    4. When BOTH exact-offer API lists are explicitly empty and vehicle
       identity matches, provider publication status becomes NOT_PUBLISHED.

    IMPORTANT:
    NOT_PUBLISHED means only that Ayvens does not publish equipment list
    items for the exact offer. It never means the vehicle has zero equipment.

    Manufacturer fallback remains downstream and separate.
    """

    def __init__(self):
        self.base = AyvensParser()
        self.details = AyvensOfferDetailsParser()
        self.equipment = AyvensEquipmentParser()
        self.identity = AyvensVehicleIdentityParser()
        self.publication = (
            AyvensEquipmentPublicationResolver()
        )

    def build(
        self,
        page,
    ) -> EvidenceAwareCompositeOffer:

        # --------------------------------------------------------
        # 1. OFFER IDENTITY / COMMERCIAL COORDINATES
        # --------------------------------------------------------

        brand = self.identity.parse_brand(
            page
        )
        model = self.identity.parse_model_name(
            page
        )
        trim = self.identity.parse_trim(
            page
        )

        fuel = self.base.parse_fuel_type(
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

        # --------------------------------------------------------
        # 2. PROVIDER DOM EQUIPMENT EVIDENCE
        # --------------------------------------------------------

        standard = (
            self.equipment
            .parse_standard_equipment(
                page
            )
        )

        optional = (
            self.equipment
            .parse_optional_equipment(
                page
            )
        )

        standard_status = (
            self._map_status(
                standard.status
            )
        )
        optional_status = (
            self._map_status(
                optional.status
            )
        )

        # --------------------------------------------------------
        # 3. EXACT-OFFER API PUBLICATION RESOLUTION
        # --------------------------------------------------------
        #
        # Do this only when the DOM did NOT yield provider-owned
        # equipment items. Provider-published equipment always wins.
        # --------------------------------------------------------

        provider_has_published_items = (
            standard_status
            == EQUIPMENT_PUBLISHED
            or optional_status
            == EQUIPMENT_PUBLISHED
        )

        if not provider_has_published_items:
            resolution = (
                self.publication.resolve(
                    page,
                    offer,
                )
            )

            if (
                resolution.status
                == PROVIDER_EQUIPMENT_NOT_PUBLISHED
            ):
                # Exact-offer provider API explicitly has no published
                # basic/extra equipment list. Preserve equipment as unknown
                # at vehicle-fact level; only publication state changes.
                standard_status = (
                    EQUIPMENT_NOT_PUBLISHED
                )
                optional_status = (
                    EQUIPMENT_NOT_PUBLISHED
                )

            elif (
                resolution.status
                == PROVIDER_EQUIPMENT_PUBLISHED
            ):
                # The provider API says equipment is published, but this
                # builder has no trustworthy item extraction from that API.
                # Therefore preserve parsing uncertainty.
                if (
                    standard_status
                    != EQUIPMENT_PUBLISHED
                ):
                    standard_status = (
                        EQUIPMENT_PARSING_UNRESOLVED
                    )

                if (
                    optional_status
                    != EQUIPMENT_PUBLISHED
                ):
                    optional_status = (
                        EQUIPMENT_PARSING_UNRESOLVED
                    )

            # UNRESOLVED publication resolution deliberately changes nothing.

        # --------------------------------------------------------
        # 4. OTHER EXACT-OFFER DIMENSIONS
        # --------------------------------------------------------

        services = (
            self.details.parse_services(
                page
            )
        )

        financial = (
            self.details
            .build_financial_conditions(
                page,
                fee,
            )
        )

        # --------------------------------------------------------
        # 5. COMPOSITE VEHICLE
        # --------------------------------------------------------
        #
        # Only actually parsed equipment items are attached here.
        # Empty/unresolved/non-published states never fabricate items.
        # --------------------------------------------------------

        standard_items = (
            standard.items
            if (
                standard_status
                == EQUIPMENT_PUBLISHED
            )
            else []
        )

        optional_items = (
            optional.items
            if (
                optional_status
                == EQUIPMENT_PUBLISHED
            )
            else []
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
            standard_equipment=standard_items,
            optional_equipment=optional_items,
        )

        composite = CompositeOffer(
            offer=offer,
            vehicle=vehicle,
            services=services,
            financial=financial,
        )

        return EvidenceAwareCompositeOffer(
            composite=composite,
            equipment_evidence=(
                EquipmentEvidenceStatus(
                    standard_status=(
                        standard_status
                    ),
                    optional_status=(
                        optional_status
                    ),
                )
            ),
        )

    def parse_quote_capabilities(
        self,
        page,
    ):
        """
        Quote controls remain capability metadata only.
        They are not observed priced contract variants.
        """
        return (
            self.details
            .parse_quote_capabilities(
                page
            )
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

    @staticmethod
    def _map_status(
        status: str,
    ) -> str:

        mapping = {
            AYVENS_PUBLISHED: (
                EQUIPMENT_PUBLISHED
            ),
            AYVENS_NOT_PUBLISHED: (
                EQUIPMENT_NOT_PUBLISHED
            ),
            AYVENS_UNRESOLVED: (
                EQUIPMENT_PARSING_UNRESOLVED
            ),
        }

        if status not in mapping:
            raise ValueError(
                "Unsupported Ayvens "
                "equipment status: "
                f"{status}"
            )

        return mapping[status]
