from dataclasses import asdict, dataclass
from typing import Dict, Tuple

IMPACT_CRITICAL = "CRITICAL"
IMPACT_HIGH = "HIGH"
IMPACT_MEDIUM = "MEDIUM"

@dataclass(frozen=True)
class EvidenceGapAction:
    rank: int
    dimension: str
    impact: str
    reason_codes: Tuple[str, ...]
    action: str
    unlock_effect: str
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class EvidenceUnlockStep:
    step: int
    resolved_dimension: str
    remaining_dimensions: Tuple[str, ...]
    price_comparison_may_be_possible: bool
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class EvidenceGapPlan:
    actions: Tuple[EvidenceGapAction, ...]
    unlock_path: Tuple[EvidenceUnlockStep, ...]
    unresolved_dimensions: Tuple[str, ...]
    diagnostic: str
    def to_dict(self): return asdict(self)

class EvidenceGapPrioritizerV1:
    DIMENSION_ORDER = ("CONTRACT","FINANCIAL","SERVICES","EQUIPMENT_VARIANT","OTHER")
    DIMENSION_CONFIG: Dict[str, dict] = {
        "CONTRACT": {
            "impact": IMPACT_CRITICAL,
            "reasons": {"NO_COMMON_PRICED_CONTRACT_STATE","CONTRACT_NORMALIZATION_INCOMPLETE"},
            "action": "Obtain one exact explicitly priced contract coordinate published for both providers.",
            "unlock_effect": "Removes the contract-coordinate barrier, but other evidence dimensions may still block price comparison.",
        },
        "FINANCIAL": {
            "impact": IMPACT_CRITICAL,
            "reasons": {"DOWN_PAYMENT_EVIDENCE_INCOMPLETE","DOWN_PAYMENT_MISMATCH"},
            "action": "Obtain explicit down-payment evidence for both offers at comparable scope.",
            "unlock_effect": "Removes the financial-condition barrier if the observed conditions are comparable.",
        },
        "SERVICES": {
            "impact": IMPACT_HIGH,
            "reasons": {"SERVICE_PARTIAL_EQUIVALENCE","SERVICE_SEMANTIC_EQUIVALENCE_INCOMPLETE","SERVICE_SEMANTIC_EVIDENCE_INCOMPLETE","SERVICE_SEMANTIC_MISMATCH"},
            "action": "Verify remaining one-sided service semantics at exact-offer scope and determine whether the packages are equivalent.",
            "unlock_effect": "Removes the service-equivalence barrier only if the remaining semantics are resolved as comparable.",
        },
        "EQUIPMENT_VARIANT": {
            "impact": IMPACT_HIGH,
            "reasons": {"VEHICLE_VARIANT_DIFFERENCE","VARIANT_VALUE_DIFFERENCE","VARIANT_EQUIVALENCE_EVIDENCE_INCOMPLETE","EQUIPMENT_EVIDENCE_INCOMPLETE","EQUIPMENT_VALUE_DIFFERENCE","VARIANT_EQUIPMENT_VALUE_DIFFERENCE"},
            "action": "Obtain complete trusted equipment evidence for both exact advertised variants and resolve the remaining variant-value difference.",
            "unlock_effect": "Removes the variant/equipment barrier only if the resulting evidence establishes an acceptable comparison basis.",
        },
    }

    def prioritize(self, decision_reasons) -> EvidenceGapPlan:
        reasons = tuple(str(x) for x in (decision_reasons or ()) if x)
        matched = set()
        dims = []
        for dimension in self.DIMENSION_ORDER[:-1]:
            cfg = self.DIMENSION_CONFIG[dimension]
            rs = tuple(r for r in reasons if r in cfg["reasons"])
            if rs:
                matched.update(rs)
                dims.append((dimension,cfg,rs))
        unknown = tuple(r for r in reasons if r not in matched)
        if unknown:
            dims.append(("OTHER",{
                "impact":IMPACT_MEDIUM,
                "action":"Review the remaining unmapped comparison blockers before allowing price ranking.",
                "unlock_effect":"Unknown blockers must be resolved explicitly; their decision impact is not inferred.",
            },unknown))
        actions = tuple(EvidenceGapAction(i,d,cfg["impact"],rs,cfg["action"],cfg["unlock_effect"]) for i,(d,cfg,rs) in enumerate(dims,1))
        remaining = [a.dimension for a in actions]
        steps = []
        for i,a in enumerate(actions,1):
            remaining.remove(a.dimension)
            steps.append(EvidenceUnlockStep(i,a.dimension,tuple(remaining),len(remaining)==0))
        diagnostic = (
            "No evidence-gap action was derived from the supplied decision reasons."
            if not actions else
            f"{len(actions)} prioritized evidence dimension(s) derived from current decision reasons. Unlock path is conditional and does not declare a price winner."
        )
        return EvidenceGapPlan(actions,tuple(steps),tuple(a.dimension for a in actions),diagnostic)
