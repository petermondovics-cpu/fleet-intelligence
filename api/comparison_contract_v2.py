from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Tuple

from api.comparison_contract import (
    BlockerDTO,
    ComparisonResponseV1,
    ContractDTO,
    DimensionStatusDTO,
    DownPaymentDTO,
    EvidenceDTO,
    OfferDTO,
    PriceDTO,
    VehicleDTO,
)

API_VERSION_V2 = "comparison.v2"

@dataclass(frozen=True)
class ObservedPriceDifferenceDTO:
    lower_provider: Optional[str]
    difference_huf: Optional[int]
    difference_percent: Optional[float]
    normalized: bool

@dataclass(frozen=True)
class DecisionDTO:
    verdict: str
    price_winner: Optional[str]
    price_comparison_allowed: bool
    observed_price_difference: ObservedPriceDifferenceDTO
    decision_reasons: Tuple[str, ...]
    confidence: int
    management_summary: str
    next_best_action: str

@dataclass(frozen=True)
class ComparisonResponseV2:
    api_version: str
    status: str
    price_comparison_allowed: bool
    price_winner: Optional[str]
    left_offer: OfferDTO
    right_offer: OfferDTO
    dimensions: DimensionStatusDTO
    blockers: Tuple[BlockerDTO, ...]
    contract_normalization_method: str
    contract_normalization_confidence: int
    equipment_score_left: Optional[int]
    equipment_score_right: Optional[int]
    decision: DecisionDTO

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_v1(self) -> ComparisonResponseV1:
        return ComparisonResponseV1(
            api_version="comparison.v1",
            status=self.status,
            price_comparison_allowed=self.price_comparison_allowed,
            price_winner=self.price_winner,
            left_offer=self.left_offer,
            right_offer=self.right_offer,
            dimensions=self.dimensions,
            blockers=self.blockers,
            contract_normalization_method=self.contract_normalization_method,
            contract_normalization_confidence=self.contract_normalization_confidence,
            equipment_score_left=self.equipment_score_left,
            equipment_score_right=self.equipment_score_right,
        )
