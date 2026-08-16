from dataclasses import dataclass
from typing import Callable, List, Optional

from models.offer import Offer
from models.contract_discovery import DiscoveredContract
from contract_collection.engine import (
    ContractCollectionEngine,
    ContractCollectionResult,
)


@dataclass(frozen=True)
class LiveCollectionResult:
    provider: str
    url: str
    results: List[ContractCollectionResult]

    @property
    def offers(self) -> List[Offer]:
        return [
            result.offer
            for result in self.results
            if (
                result.status == "COLLECTED"
                and result.offer is not None
            )
        ]


class LiveContractCollector:
    """
    Provider-neutral adapter around ContractCollectionEngine.

    The provider scraper remains responsible for:
      1. selecting a discovered contract;
      2. parsing the selected page.

    This class only orchestrates the two operations and
    returns validated Offers.
    """

    def __init__(self):
        self.engine = ContractCollectionEngine()

    def collect(
        self,
        provider: str,
        url: str,
        contracts: List[DiscoveredContract],
        select_contract: Callable[
            [DiscoveredContract],
            None,
        ],
        parse_selected_contract: Callable[
            [DiscoveredContract],
            Offer,
        ],
    ) -> LiveCollectionResult:

        results = self.engine.collect(
            contracts=contracts,
            select_contract=select_contract,
            parse_selected_contract=parse_selected_contract,
        )

        return LiveCollectionResult(
            provider=provider,
            url=url,
            results=results,
        )
