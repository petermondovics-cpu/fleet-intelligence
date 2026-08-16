from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Tuple


API_VERSION = "comparison.v1"


@dataclass(frozen=True)
class EvidenceDTO:
    status: str
    source_url: Optional[str] = None
    source_text: Optional[str] = None


@dataclass(frozen=True)
class DownPaymentDTO:
    status: str
    percent: Optional[float]
    amount_huf: Optional[int]
    evidence: EvidenceDTO


@dataclass(frozen=True)
class PriceDTO:
    advertised_monthly_fee_huf: Optional[int]
    comparable_monthly_fee_huf: Optional[int]
    down_payment: DownPaymentDTO
    pricing_basis: Optional[str] = None


@dataclass(frozen=True)
class ContractDTO:
    duration_months: Optional[int]
    mileage_km_per_year: Optional[int]


@dataclass(frozen=True)
class VehicleDTO:
    brand: Optional[str]
    model: Optional[str]
    trim: Optional[str]
    fuel_type: Optional[str]


@dataclass(frozen=True)
class OfferDTO:
    provider: str
    vehicle: VehicleDTO
    contract: ContractDTO
    price: PriceDTO
    source_url: Optional[str]


@dataclass(frozen=True)
class DimensionStatusDTO:
    vehicle: str
    variant: str
    services: str
    equipment: str
    contract: str
    financial: str


@dataclass(frozen=True)
class BlockerDTO:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class ComparisonResponseV1:
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

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
