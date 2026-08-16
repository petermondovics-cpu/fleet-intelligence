from pathlib import Path

path = Path("comparison/evidence_enrichment_bridge.py")
text = path.read_text()

backup = path.with_suffix(".py.pre_financial_v3")
backup.write_text(text)

# ------------------------------------------------------------
# 1. Financial imports
# ------------------------------------------------------------

old = '''from models.financial_conditions import (
    EVIDENCE_OBSERVED,
    FinancialEvidence,
    ServiceItem,
    ServicePackage,
)'''

new = '''from models.financial_conditions import (
    EVIDENCE_OBSERVED,
    FinancialEvidence,
    FinancialConditions,
    DownPayment,
    ServiceItem,
    ServicePackage,
)'''

if old not in text:
    raise RuntimeError("financial import block not found")

text = text.replace(old, new, 1)

# ------------------------------------------------------------
# 2. EnrichedFinancialEvidence
# ------------------------------------------------------------

marker = '''@dataclass(frozen=True)
class EnrichedComparisonContext:'''

insert = '''@dataclass(frozen=True)
class EnrichedFinancialEvidence:
    provider: str
    usable_status: str
    financial: FinancialConditions
    source_url: Optional[str]
    pricing_basis: Optional[str]
    acquisition_used: bool
    diagnostic: str


@dataclass(frozen=True)
class EnrichedComparisonContext:'''

if marker not in text:
    raise RuntimeError("EnrichedComparisonContext marker not found")

text = text.replace(marker, insert, 1)

# ------------------------------------------------------------
# 3. Extend context
# ------------------------------------------------------------

old = '''    left_services: EnrichedServiceEvidence
    right_services: EnrichedServiceEvidence'''

new = '''    left_services: EnrichedServiceEvidence
    right_services: EnrichedServiceEvidence
    left_financial: EnrichedFinancialEvidence
    right_financial: EnrichedFinancialEvidence'''

if old not in text:
    raise RuntimeError("context service fields not found")

text = text.replace(old, new, 1)

# ------------------------------------------------------------
# 4. Extend enrich()
# ------------------------------------------------------------

old = '''            left_services=self._services_for_side(left, candidates),
            right_services=self._services_for_side(right, candidates),
        )'''

new = '''            left_services=self._services_for_side(left, candidates),
            right_services=self._services_for_side(right, candidates),
            left_financial=self._financial_for_side(left, candidates),
            right_financial=self._financial_for_side(right, candidates),
        )'''

if old not in text:
    raise RuntimeError("enrich return block not found")

text = text.replace(old, new, 1)

# ------------------------------------------------------------
# 5. Financial enrichment implementation
# ------------------------------------------------------------

marker = '''    # ============================================================
    # SERVICES
    # ============================================================'''

financial_code = '''    # ============================================================
    # FINANCIAL
    # ============================================================

    def _financial_for_side(
        self,
        side,
        candidates,
    ) -> EnrichedFinancialEvidence:

        provider = side.composite.provider
        original = side.composite.financial

        financial_candidates = tuple(
            c for c in candidates
            if (
                c.target_dimension == "FINANCIAL"
                and c.provider.strip().casefold()
                == provider.strip().casefold()
            )
        )

        for candidate in financial_candidates:
            payload = candidate.payload

            # Financial evidence may affect price comparison only when
            # explicitly scoped to the exact advertised offer.
            if payload.get("applicability_scope") != "EXACT_OFFER":
                continue

            percent = payload.get("down_payment_percent")
            monthly_fee = payload.get("monthly_fee")

            if percent is None:
                continue

            # A discovered financial state without its directly observed
            # monthly fee must not replace the advertised financial view.
            if monthly_fee is None:
                continue

            evidence = FinancialEvidence(
                status=EVIDENCE_OBSERVED,
                source_url=candidate.source_url,
                source_text=candidate.source_text,
            )

            enriched = FinancialConditions(
                monthly_fee=int(monthly_fee),
                down_payment=DownPayment(
                    percent=float(percent),
                    amount=None,
                    status=EVIDENCE_OBSERVED,
                    evidence=evidence,
                ),
                other_one_off_fees=original.other_one_off_fees,
                other_recurring_fees=original.other_recurring_fees,
                monthly_fee_evidence=evidence,
            )

            return EnrichedFinancialEvidence(
                provider=provider,
                usable_status="ENRICHED_PROVIDER_EVIDENCE",
                financial=enriched,
                source_url=candidate.source_url,
                pricing_basis=payload.get("pricing_basis"),
                acquisition_used=True,
                diagnostic=(
                    "Validated exact-offer financial evidence was promoted "
                    "into an immutable enriched comparison view."
                ),
            )

        return EnrichedFinancialEvidence(
            provider=provider,
            usable_status="ORIGINAL_ONLY",
            financial=original,
            source_url=None,
            pricing_basis=None,
            acquisition_used=False,
            diagnostic=(
                "No validated exact-offer financial acquisition evidence "
                "was promoted."
            ),
        )

'''

if marker not in text:
    raise RuntimeError("SERVICES marker not found")

text = text.replace(marker, financial_code + marker, 1)

compile(text, str(path), "exec")
path.write_text(text)

print(f"PATCHED: {path}")
print(f"BACKUP : {backup}")
print("FINANCIAL ENRICHMENT BRIDGE V3 APPLIED")
