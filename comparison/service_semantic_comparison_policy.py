from dataclasses import dataclass
from typing import Tuple

from comparison.service_semantic_equivalence import (
    SEMANTIC_DIFFERENCE,
    SEMANTIC_INSUFFICIENT_EVIDENCE,
    SEMANTIC_MATCH,
    SEMANTIC_PARTIAL_EQUIVALENCE,
    ServiceSemanticEquivalenceAssessor,
)


@dataclass(frozen=True)
class ServiceSemanticBarrier:
    code: str
    message: str
    hard: bool = False


@dataclass(frozen=True)
class ServiceSemanticPolicyResult:
    status: str
    price_comparison_safe: bool
    barriers: Tuple[
        ServiceSemanticBarrier,
        ...
    ]
    semantic_result: object


class ServiceSemanticComparisonPolicy:
    """
    Translation layer from semantic service assessment to full-comparison
    blockers.

    This does not yet mutate FullComparisonOrchestrator automatically.
    It provides the exact policy output for integration/regression testing.

    V1 policy:
    - MATCH => no service blocker.
    - explicit contradiction => hard SERVICE_SEMANTIC_MISMATCH.
    - PARTIAL_EQUIVALENCE => one consolidated non-hard blocker plus
      explicit unresolved semantic codes.
    - insufficient evidence => consolidated evidence blocker.
    """

    def __init__(self):
        self.assessor = (
            ServiceSemanticEquivalenceAssessor()
        )

    def evaluate(
        self,
        left_package,
        right_package,
    ) -> ServiceSemanticPolicyResult:

        result = (
            self.assessor.assess(
                left_package,
                right_package,
            )
        )

        barriers = []

        if (
            result.status
            == SEMANTIC_DIFFERENCE
        ):
            for item in (
                result.contradictions
            ):
                barriers.append(
                    ServiceSemanticBarrier(
                        code=(
                            "SERVICE_SEMANTIC_MISMATCH"
                        ),
                        message=(
                            f"Canonical service {item.code} has an "
                            "explicit inclusion contradiction."
                        ),
                        hard=True,
                    )
                )

        elif (
            result.status
            == SEMANTIC_PARTIAL_EQUIVALENCE
        ):
            unresolved = (
                tuple(
                    f"LEFT:{code}"
                    for code
                    in result.left_only_codes
                )
                + tuple(
                    f"RIGHT:{code}"
                    for code
                    in result.right_only_codes
                )
            )

            barriers.append(
                ServiceSemanticBarrier(
                    code=(
                        "SERVICE_SEMANTIC_EQUIVALENCE_INCOMPLETE"
                    ),
                    message=(
                        "Core service semantics match, but additional "
                        "one-sided published semantics remain unresolved: "
                        + ", ".join(
                            unresolved
                        )
                        + "."
                    ),
                    hard=False,
                )
            )

        elif (
            result.status
            == SEMANTIC_INSUFFICIENT_EVIDENCE
        ):
            barriers.append(
                ServiceSemanticBarrier(
                    code=(
                        "SERVICE_SEMANTIC_EVIDENCE_INCOMPLETE"
                    ),
                    message=(
                        result.diagnostic
                    ),
                    hard=False,
                )
            )

        elif (
            result.status
            != SEMANTIC_MATCH
        ):
            raise ValueError(
                "Unsupported semantic service status: "
                + str(
                    result.status
                )
            )

        return (
            ServiceSemanticPolicyResult(
                status=result.status,
                price_comparison_safe=(
                    result.status
                    == SEMANTIC_MATCH
                ),
                barriers=tuple(
                    barriers
                ),
                semantic_result=result,
            )
        )
