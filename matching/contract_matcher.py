from dataclasses import dataclass

from models.offer import Offer


@dataclass
class ContractMatch:
    duration_match: bool
    mileage_match: bool

    comparable: bool

    duration_difference: int
    mileage_difference: int

    duration_similarity: int
    mileage_similarity: int
    contract_similarity: int

    difference: str


class ContractMatcher:

    def match(
        self,
        offer_a: Offer,
        offer_b: Offer,
    ) -> ContractMatch:

        duration_difference = abs(
            offer_a.duration
            - offer_b.duration
        )

        mileage_difference = abs(
            offer_a.mileage
            - offer_b.mileage
        )

        duration_match = (
            duration_difference == 0
        )

        mileage_match = (
            mileage_difference == 0
        )

        comparable = (
            duration_match
            and mileage_match
        )

        duration_similarity = (
            self._duration_similarity(
                duration_difference
            )
        )

        mileage_similarity = (
            self._mileage_similarity(
                mileage_difference
            )
        )

        contract_similarity = round(
            (
                duration_similarity * 0.60
                +
                mileage_similarity * 0.40
            )
        )

        differences = []

        if not duration_match:

            differences.append(
                f"futamidő: "
                f"{offer_a.duration} vs "
                f"{offer_b.duration} hónap"
            )

        if not mileage_match:

            differences.append(
                f"futásteljesítmény: "
                f"{offer_a.mileage:,} vs "
                f"{offer_b.mileage:,} km/év"
            )

        return ContractMatch(
            duration_match=duration_match,
            mileage_match=mileage_match,
            comparable=comparable,
            duration_difference=duration_difference,
            mileage_difference=mileage_difference,
            duration_similarity=duration_similarity,
            mileage_similarity=mileage_similarity,
            contract_similarity=contract_similarity,
            difference="; ".join(
                differences
            ),
        )

    def _duration_similarity(
        self,
        difference: int,
    ) -> int:

        if difference == 0:
            return 100

        if difference <= 12:
            return 85

        if difference <= 24:
            return 70

        if difference <= 36:
            return 55

        return 40

    def _mileage_similarity(
        self,
        difference: int,
    ) -> int:

        if difference == 0:
            return 100

        if difference <= 5000:
            return 90

        if difference <= 10000:
            return 80

        if difference <= 15000:
            return 70

        return 60