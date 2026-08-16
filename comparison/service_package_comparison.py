from dataclasses import dataclass
from typing import Tuple

from comparison.service_package_normalizer import (
    ServicePackageNormalizer,
)


SERVICE_MATCH = "MATCH"
SERVICE_DIFFERENCE = "DIFFERENCE"
SERVICE_INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class ServiceDifference:
    code: str
    left_included: object
    right_included: object


@dataclass(frozen=True)
class ServiceComparisonResult:
    status: str
    differences: Tuple[ServiceDifference, ...]
    left_unknown: Tuple[str, ...]
    right_unknown: Tuple[str, ...]
    left_only_codes: Tuple[str, ...]
    right_only_codes: Tuple[str, ...]


class ServicePackageComparisonEngine:
    """
    Canonical service comparison V1.

    Rules:
    - explicit True vs False on the same canonical service => DIFFERENCE
    - None is never treated as False
    - unknown provider wording => INSUFFICIENT_EVIDENCE
    - service code present on only one side => INSUFFICIENT_EVIDENCE,
      not automatic exclusion
    - exact canonical coverage with no contradiction => MATCH
    """

    def __init__(self):
        self.normalizer = (
            ServicePackageNormalizer()
        )

    def compare(
        self,
        left_package,
        right_package,
    ) -> ServiceComparisonResult:

        left = self.normalizer.normalize(
            left_package
        )

        right = self.normalizer.normalize(
            right_package
        )

        lmap = left.by_code()
        rmap = right.by_code()

        common = (
            set(lmap)
            & set(rmap)
        )

        differences = []

        for code in sorted(common):

            l = lmap[code]
            r = rmap[code]

            if (
                l.included is not None
                and r.included is not None
                and l.included != r.included
            ):
                differences.append(
                    ServiceDifference(
                        code=code,
                        left_included=l.included,
                        right_included=r.included,
                    )
                )

        left_only = tuple(
            sorted(
                set(lmap)
                - set(rmap)
            )
        )

        right_only = tuple(
            sorted(
                set(rmap)
                - set(lmap)
            )
        )

        if differences:
            status = SERVICE_DIFFERENCE

        elif (
            left.unknown_items
            or right.unknown_items
            or left_only
            or right_only
            or any(
                lmap[code].included is None
                or rmap[code].included is None
                for code in common
            )
        ):
            status = (
                SERVICE_INSUFFICIENT_EVIDENCE
            )

        else:
            status = SERVICE_MATCH

        return ServiceComparisonResult(
            status=status,
            differences=tuple(
                differences
            ),
            left_unknown=left.unknown_items,
            right_unknown=right.unknown_items,
            left_only_codes=left_only,
            right_only_codes=right_only,
        )
