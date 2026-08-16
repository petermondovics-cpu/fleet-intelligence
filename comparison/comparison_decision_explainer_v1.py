from dataclasses import asdict, dataclass
from typing import Optional, Tuple

PRICE_COMPARABLE = "PRICE_COMPARABLE"
NOT_PRICE_COMPARABLE = "NOT_PRICE_COMPARABLE"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

@dataclass(frozen=True)
class ObservedPriceDifference:
    lower_provider: Optional[str]
    difference_huf: Optional[int]
    difference_percent: Optional[float]
    normalized: bool = False

@dataclass(frozen=True)
class ComparisonDecisionExplanation:
    verdict: str
    price_winner: Optional[str]
    price_comparison_allowed: bool
    observed_price_difference: ObservedPriceDifference
    decision_reasons: Tuple[str, ...]
    next_best_action: str
    management_summary: str
    confidence: int

    def to_dict(self):
        return asdict(self)

class ComparisonDecisionExplainerV1:
    REASON_MAP = {
        "CONTRACT_NORMALIZATION_INCOMPLETE": "NO_COMMON_PRICED_CONTRACT_STATE",
        "VARIANT_EQUIPMENT_VALUE_DIFFERENCE": "VARIANT_VALUE_DIFFERENCE",
        "EQUIPMENT_VALUE_DIFFERENCE": "EQUIPMENT_VALUE_DIFFERENCE",
        "SERVICE_SEMANTIC_EQUIVALENCE_INCOMPLETE": "SERVICE_PARTIAL_EQUIVALENCE",
        "DOWN_PAYMENT_EVIDENCE_INCOMPLETE": "DOWN_PAYMENT_EVIDENCE_INCOMPLETE",
        "DOWN_PAYMENT_MISMATCH": "DOWN_PAYMENT_MISMATCH",
        "VEHICLE_VARIANT_DIFFERENCE": "VEHICLE_VARIANT_DIFFERENCE",
    }

    def explain(self, final, left, right):
        allowed = bool(final.price_comparison_allowed)
        codes = tuple(getattr(x, "code", "") for x in getattr(final, "barriers", ()))
        if allowed:
            verdict = PRICE_COMPARABLE
        elif self._evidence_gap(codes):
            verdict = INSUFFICIENT_EVIDENCE
        else:
            verdict = NOT_PRICE_COMPARABLE

        observed = self._observed_difference(left, right)
        reasons = self._reasons(codes)
        return ComparisonDecisionExplanation(
            verdict=verdict,
            price_winner=final.price_winner if allowed else None,
            price_comparison_allowed=allowed,
            observed_price_difference=observed,
            decision_reasons=reasons,
            next_best_action=self._next_action(codes, left, right),
            management_summary=self._summary(verdict, final, left, right, observed, reasons),
            confidence=self._confidence(verdict, final),
        )

    @staticmethod
    def _evidence_gap(codes):
        return any(x in {
            "CONTRACT_NORMALIZATION_INCOMPLETE",
            "DOWN_PAYMENT_EVIDENCE_INCOMPLETE",
            "VARIANT_EQUIVALENCE_EVIDENCE_INCOMPLETE",
            "EQUIPMENT_EVIDENCE_INCOMPLETE",
            "SERVICE_SEMANTIC_EQUIVALENCE_INCOMPLETE",
        } for x in codes)

    @classmethod
    def _reasons(cls, codes):
        out = []
        for code in codes:
            value = cls.REASON_MAP.get(code, code)
            if value and value not in out:
                out.append(value)
        return tuple(out)

    @staticmethod
    def _offer(side):
        return getattr(getattr(side, "composite", None), "offer", None)

    @classmethod
    def _provider(cls, side):
        offer = cls._offer(side)
        return getattr(side, "provider", None) or getattr(offer, "provider", None) or "Unknown"

    @classmethod
    def _fee(cls, side):
        offer = cls._offer(side)
        for obj in (offer, getattr(side, "composite", None), side):
            if obj is None:
                continue
            for attr in ("monthly_fee", "monthly_fee_huf", "price"):
                value = getattr(obj, attr, None)
                if isinstance(value, (int, float)):
                    return int(round(value))
        return None

    @classmethod
    def _contract(cls, side):
        offer = cls._offer(side)
        if offer is None:
            return None, None
        duration = getattr(offer, "duration", None) or getattr(offer, "duration_months", None)
        mileage = (getattr(offer, "mileage", None) or
                   getattr(offer, "annual_mileage", None) or
                   getattr(offer, "mileage_per_year", None))
        return duration, mileage

    @classmethod
    def _observed_difference(cls, left, right):
        lp, rp = cls._fee(left), cls._fee(right)
        if lp is None or rp is None:
            return ObservedPriceDifference(None, None, None, False)
        if lp == rp:
            return ObservedPriceDifference("TIE", 0, 0.0, False)
        if lp < rp:
            provider, lower, higher = cls._provider(left), lp, rp
        else:
            provider, lower, higher = cls._provider(right), rp, lp
        diff = higher - lower
        pct = round(diff / higher * 100, 2) if higher else None
        return ObservedPriceDifference(provider, diff, pct, False)

    @classmethod
    def _next_action(cls, codes, left, right):
        if "CONTRACT_NORMALIZATION_INCOMPLETE" in codes:
            ld, lm = cls._contract(left)
            rd, rm = cls._contract(right)
            lp, rp = cls._provider(left), cls._provider(right)
            if ld and lm and rd and rm:
                return (f"Obtain an explicit {rp} price for {ld} months / {lm} km/year "
                        f"or an explicit {lp} price for {rd} months / {rm} km/year.")
            return "Obtain one exact explicitly priced contract coordinate published for both providers."
        if "DOWN_PAYMENT_EVIDENCE_INCOMPLETE" in codes:
            return "Obtain explicit down-payment evidence for the provider whose condition remains unpublished or unresolved."
        if "SERVICE_SEMANTIC_EQUIVALENCE_INCOMPLETE" in codes:
            return "Verify the remaining one-sided service semantics at exact-offer scope."
        if ("EQUIPMENT_EVIDENCE_INCOMPLETE" in codes or
                "VARIANT_EQUIVALENCE_EVIDENCE_INCOMPLETE" in codes):
            return "Obtain complete trusted equipment evidence for both exact advertised variants."
        return "No additional evidence action is required for price comparison."

    @classmethod
    def _summary(cls, verdict, final, left, right, observed, reasons):
        lp, rp = cls._fee(left), cls._fee(right)
        lprov, rprov = cls._provider(left), cls._provider(right)
        if lp is not None and rp is not None:
            price = f"The published monthly fees are {lprov}: {lp:,} Ft and {rprov}: {rp:,} Ft.".replace(",", " ")
        else:
            price = "Both published monthly fees are not available."
        if observed.lower_provider not in (None, "TIE"):
            diff = (f" {observed.lower_provider} has the lower observed nominal monthly fee "
                    f"by {observed.difference_huf:,} Ft ({observed.difference_percent:.2f}%).").replace(",", " ")
        elif observed.lower_provider == "TIE":
            diff = " The observed nominal monthly fees are equal."
        else:
            diff = ""
        if final.price_comparison_allowed:
            conclusion = " The comparison engine allows normalized price comparison."
        else:
            conclusion = " This is not a normalized price advantage and no price winner can be declared from the current evidence."
        reason = " Decision reasons: " + ", ".join(reasons) + "." if reasons else ""
        return f"{verdict}. {price}{diff}{conclusion}{reason}"

    @staticmethod
    def _confidence(verdict, final):
        if verdict == PRICE_COMPARABLE:
            return 100
        if verdict == INSUFFICIENT_EVIDENCE:
            return max(0, min(99, int(getattr(final, "contract_normalization_confidence", 0) or 0)))
        return 100
