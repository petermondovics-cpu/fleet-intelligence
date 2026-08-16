from dataclasses import dataclass


EQUIPMENT_PUBLISHED = "PUBLISHED"
EQUIPMENT_NOT_PUBLISHED = "NOT_PUBLISHED"
EQUIPMENT_PARSING_UNRESOLVED = "PARSING_UNRESOLVED"


@dataclass(frozen=True)
class EquipmentEvidenceStatus:
    """
    Provider-level evidence status for vehicle equipment.

    This is deliberately separate from the equipment item lists.

    Why:
    [] + NOT_PUBLISHED
        means the provider does not publish the list.

    [] + PUBLISHED
        means the provider explicitly publishes an empty list.

    [] + PARSING_UNRESOLVED
        means the page likely contains equipment information,
        but the parser could not safely extract it.
    """

    standard_status: str
    optional_status: str

    def __post_init__(self):

        allowed = {
            EQUIPMENT_PUBLISHED,
            EQUIPMENT_NOT_PUBLISHED,
            EQUIPMENT_PARSING_UNRESOLVED,
        }

        if self.standard_status not in allowed:
            raise ValueError(
                "Invalid standard equipment evidence status: "
                f"{self.standard_status}"
            )

        if self.optional_status not in allowed:
            raise ValueError(
                "Invalid optional equipment evidence status: "
                f"{self.optional_status}"
            )

    @property
    def standard_comparable(self) -> bool:
        return (
            self.standard_status
            == EQUIPMENT_PUBLISHED
        )

    @property
    def optional_comparable(self) -> bool:
        return (
            self.optional_status
            == EQUIPMENT_PUBLISHED
        )

    @property
    def fully_comparable(self) -> bool:
        return (
            self.standard_comparable
            and self.optional_comparable
        )
