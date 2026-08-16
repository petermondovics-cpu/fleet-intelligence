from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class EvidenceResolutionAction:
    blocker_code: str
    action_type: str
    target_dimension: str
    priority: int
    message: str


@dataclass(frozen=True)
class EvidenceResolutionPlan:
    actions: Tuple[EvidenceResolutionAction, ...]

    @property
    def action_count(self) -> int:
        return len(self.actions)

    def by_priority(self):
        return tuple(
            sorted(
                self.actions,
                key=lambda x: (
                    x.priority,
                    x.blocker_code,
                ),
            )
        )


class EvidenceGapResolver:
    """
    Evidence Gap Resolver V1.

    Converts FullComparisonOrchestrator blocker codes into concrete
    evidence-acquisition tasks.

    Design rules:
    - never invent missing evidence;
    - preserve distinction between provider-published evidence and
      manufacturer/specification evidence;
    - contract pricing evidence must be observed priced offers;
    - Ayvens quote sliders remain non-pricing metadata;
    - down payment must be explicitly observed, never assumed;
    - one blocker may produce more than one action.
    """

    def resolve(
        self,
        full_comparison_result,
    ) -> EvidenceResolutionPlan:

        actions = []

        for barrier in full_comparison_result.barriers:

            code = barrier.code

            if code == "SERVICE_EVIDENCE_INCOMPLETE":
                actions.append(
                    EvidenceResolutionAction(
                        blocker_code=code,
                        action_type="FIND_PROVIDER_SERVICE_DOCUMENTATION",
                        target_dimension="SERVICES",
                        priority=20,
                        message=(
                            "Find provider-published service documentation "
                            "that explicitly confirms whether the one-sided "
                            "canonical services are included or excluded."
                        ),
                    )
                )

            elif code == "SERVICE_LEFT_ONLY_PUBLISHED":
                actions.append(
                    EvidenceResolutionAction(
                        blocker_code=code,
                        action_type="VERIFY_RIGHT_PROVIDER_SERVICE",
                        target_dimension="SERVICES",
                        priority=25,
                        message=(
                            "Verify whether the right provider includes the "
                            "left-only canonical services, using explicit "
                            "provider documentation."
                        ),
                    )
                )

            elif code == "SERVICE_RIGHT_ONLY_PUBLISHED":
                actions.append(
                    EvidenceResolutionAction(
                        blocker_code=code,
                        action_type="VERIFY_LEFT_PROVIDER_SERVICE",
                        target_dimension="SERVICES",
                        priority=25,
                        message=(
                            "Verify whether the left provider includes the "
                            "right-only canonical services, using explicit "
                            "provider documentation."
                        ),
                    )
                )

            elif code == "SERVICE_UNKNOWN_WORDING":
                actions.append(
                    EvidenceResolutionAction(
                        blocker_code=code,
                        action_type="NORMALIZE_SERVICE_WORDING",
                        target_dimension="SERVICES",
                        priority=15,
                        message=(
                            "Review the unknown service wording and map it "
                            "to a canonical service only when semantics are "
                            "explicitly supported."
                        ),
                    )
                )

            elif code == "EQUIPMENT_EVIDENCE_INCOMPLETE":
                actions.append(
                    EvidenceResolutionAction(
                        blocker_code=code,
                        action_type="FIND_EQUIPMENT_SPECIFICATION_SOURCE",
                        target_dimension="EQUIPMENT",
                        priority=20,
                        message=(
                            "Acquire a reliable equipment specification for "
                            "the exact vehicle derivative. Prefer provider-"
                            "published evidence; otherwise use a manufacturer "
                            "specification source and mark the source type."
                        ),
                    )
                )

            elif code == "EQUIPMENT_VALUE_EVIDENCE_INCOMPLETE":
                actions.append(
                    EvidenceResolutionAction(
                        blocker_code=code,
                        action_type="EXTEND_EQUIPMENT_CANONICAL_MAP",
                        target_dimension="EQUIPMENT",
                        priority=30,
                        message=(
                            "Review currently unknown equipment items and add "
                            "canonical aliases/value rules only with explicit "
                            "semantic evidence."
                        ),
                    )
                )

            elif code == "EQUIPMENT_VALUE_DIFFERENCE":
                actions.append(
                    EvidenceResolutionAction(
                        blocker_code=code,
                        action_type="DEFINE_EQUIPMENT_VALUE_POLICY",
                        target_dimension="EQUIPMENT",
                        priority=40,
                        message=(
                            "Define a business-approved tolerance or monetary "
                            "valuation policy for canonical equipment score "
                            "differences before allowing price equivalence."
                        ),
                    )
                )

            elif code == "CONTRACT_NORMALIZATION_INCOMPLETE":
                actions.append(
                    EvidenceResolutionAction(
                        blocker_code=code,
                        action_type="COLLECT_OBSERVED_PRICED_CONTRACT_VARIANT",
                        target_dimension="CONTRACT",
                        priority=10,
                        message=(
                            "Collect an observed priced offer from the same "
                            "provider and same canonical vehicle identity that "
                            "differs only in the required contract dimension. "
                            "Quote-request slider ranges are not evidence."
                        ),
                    )
                )

            elif code == "DOWN_PAYMENT_EVIDENCE_INCOMPLETE":
                actions.append(
                    EvidenceResolutionAction(
                        blocker_code=code,
                        action_type="FIND_EXPLICIT_DOWN_PAYMENT_CONDITION",
                        target_dimension="FINANCIAL",
                        priority=10,
                        message=(
                            "Find an explicit observed down-payment percentage "
                            "or HUF amount for both offers. Do not assume 20%."
                        ),
                    )
                )

            elif code == "DOWN_PAYMENT_MISMATCH":
                actions.append(
                    EvidenceResolutionAction(
                        blocker_code=code,
                        action_type="NORMALIZE_DOWN_PAYMENT_ECONOMICS",
                        target_dimension="FINANCIAL",
                        priority=15,
                        message=(
                            "Obtain vehicle/financed-value evidence sufficient "
                            "to convert different observed down-payment terms "
                            "to a common economic basis."
                        ),
                    )
                )

            elif code in {
                "ONE_OFF_FEE_MISMATCH",
                "RECURRING_FEE_MISMATCH",
            }:
                actions.append(
                    EvidenceResolutionAction(
                        blocker_code=code,
                        action_type="NORMALIZE_ADDITIONAL_FEES",
                        target_dimension="FINANCIAL",
                        priority=15,
                        message=(
                            "Normalize explicit additional fees to a common "
                            "contract basis before price comparison."
                        ),
                    )
                )

            elif code == "VEHICLE_VARIANT_DIFFERENCE":
                actions.append(
                    EvidenceResolutionAction(
                        blocker_code=code,
                        action_type="VERIFY_VARIANT_EQUIVALENCE",
                        target_dimension="VEHICLE",
                        priority=35,
                        message=(
                            "Confirm whether the advertised variants are "
                            "economically equivalent using equipment and "
                            "powertrain specification evidence."
                        ),
                    )
                )

            elif barrier.hard:
                actions.append(
                    EvidenceResolutionAction(
                        blocker_code=code,
                        action_type="REJECT_OR_REVIEW_HARD_MISMATCH",
                        target_dimension="GENERAL",
                        priority=5,
                        message=(
                            "This blocker is a hard contradiction. Do not "
                            "attempt price comparison unless source data is "
                            "shown to be incorrect."
                        ),
                    )
                )

        # Deduplicate exact same action tuples while preserving order.
        unique = []
        seen = set()

        for action in actions:
            key = (
                action.blocker_code,
                action.action_type,
                action.target_dimension,
                action.message,
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(action)

        return EvidenceResolutionPlan(
            actions=tuple(unique)
        )
