from dataclasses import dataclass


@dataclass(frozen=True)
class ContractVariant:
    """
    Contract configuration to collect from a leasing offer page.

    duration is expressed in months.
    mileage is expressed in km/year.
    """

    duration: int
    mileage: int


DEFAULT_CONTRACT_VARIANTS = (
    ContractVariant(48, 20000),
    ContractVariant(48, 30000),
    ContractVariant(60, 20000),
    ContractVariant(60, 30000),
)
