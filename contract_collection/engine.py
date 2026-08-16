from dataclasses import dataclass
from typing import Callable, List, Optional

from models.offer import Offer
from models.contract_discovery import DiscoveredContract


@dataclass(frozen=True)
class ContractCollectionResult:
    """
    Result of collecting one discovered contract.

    An Offer is returned only when the selected contract is
    confirmed by the provider parser.
    """

    contract: DiscoveredContract
    offer: Optional[Offer]
    status: str
    reason: str = ""


class ContractCollectionEngine:
    """
    Provider-neutral orchestration for discovered contracts.

    The provider scraper supplies:
      - select_contract(contract)
      - parse_selected_contract(contract)

    The engine itself never invents duration, mileage or price.
    """

    def collect(
        self,
        contracts: List[DiscoveredContract],
        select_contract: Callable[
            [DiscoveredContract],
            None,
        ],
        parse_selected_contract: Callable[
            [DiscoveredContract],
            Offer,
        ],
    ) -> List[ContractCollectionResult]:

        results = []

        for contract in contracts:

            try:

                select_contract(
                    contract
                )

                offer = (
                    parse_selected_contract(
                        contract
                    )
                )

                if offer.duration != contract.duration:
                    raise ValueError(
                        "Duration validation failed: "
                        f"requested={contract.duration}, "
                        f"observed={offer.duration}"
                    )

                if offer.mileage != contract.mileage:
                    raise ValueError(
                        "Mileage validation failed: "
                        f"requested={contract.mileage}, "
                        f"observed={offer.mileage}"
                    )

                if offer.monthly_fee <= 0:
                    raise ValueError(
                        "Monthly fee validation failed: "
                        f"observed={offer.monthly_fee}"
                    )

                results.append(
                    ContractCollectionResult(
                        contract=contract,
                        offer=offer,
                        status="COLLECTED",
                    )
                )

            except Exception as exc:

                results.append(
                    ContractCollectionResult(
                        contract=contract,
                        offer=None,
                        status="REJECTED",
                        reason=str(exc),
                    )
                )

        return results

    @staticmethod
    def offers(
        results: List[ContractCollectionResult],
    ) -> List[Offer]:

        return [
            result.offer
            for result in results
            if (
                result.status == "COLLECTED"
                and result.offer is not None
            )
        ]
