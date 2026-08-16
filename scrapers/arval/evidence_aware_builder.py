from models.equipment_evidence import (
    EQUIPMENT_NOT_PUBLISHED,
    EquipmentEvidenceStatus,
)
from comparison.evidence_aware_comparable import (
    EvidenceAwareCompositeOffer,
)
from scrapers.arval.composite_offer_builder import (
    ArvalCompositeOfferBuilder,
)


class ArvalEvidenceAwareBuilder:
    """
    Wraps the existing Arval CompositeOffer builder with provider-level
    equipment publication evidence.

    Provider rule:
    Arval does not publish standard/optional equipment lists on the
    offer pages used by FleetIQ.
    """

    def __init__(self):
        self.composite_builder = (
            ArvalCompositeOfferBuilder()
        )

    def build(
        self,
        page,
    ) -> EvidenceAwareCompositeOffer:

        composite = (
            self.composite_builder.build(
                page
            )
        )

        return EvidenceAwareCompositeOffer(
            composite=composite,
            equipment_evidence=(
                EquipmentEvidenceStatus(
                    standard_status=(
                        EQUIPMENT_NOT_PUBLISHED
                    ),
                    optional_status=(
                        EQUIPMENT_NOT_PUBLISHED
                    ),
                )
            ),
        )
