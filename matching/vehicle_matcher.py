import re
from dataclasses import dataclass

from normalizers.vehicle_normalizer import (
    VehicleNormalizer,
)


@dataclass
class VehicleMatch:

    brand_match: bool
    model_match: bool
    powertrain_match: bool

    confidence: int

    match_type: str


class VehicleMatcher:

    def __init__(self):

        self.normalizer = (
            VehicleNormalizer()
        )

    # ------------------------------------------------
    # MATCH
    # ------------------------------------------------

    def match(
        self,
        brand_a: str,
        model_a: str,
        fuel_a: str,
        brand_b: str,
        model_b: str,
        fuel_b: str,
    ) -> VehicleMatch:

        normalized_brand_a = (
            self.normalizer.normalize_brand(
                brand_a
            )
        )

        normalized_brand_b = (
            self.normalizer.normalize_brand(
                brand_b
            )
        )

        normalized_model_a = (
            self.normalizer.normalize_model(
                model_a
            )
        )

        normalized_model_b = (
            self.normalizer.normalize_model(
                model_b
            )
        )

        normalized_fuel_a = (
            self.normalizer.normalize_fuel_type(
                fuel_a
            )
        )

        normalized_fuel_b = (
            self.normalizer.normalize_fuel_type(
                fuel_b
            )
        )

        brand_match = (
            normalized_brand_a
            == normalized_brand_b
        )

        model_match = (
            normalized_model_a
            == normalized_model_b
        )

        powertrain_match = (
            normalized_fuel_a
            == normalized_fuel_b
        )

        # ------------------------------------------------
        # NO MATCH
        # ------------------------------------------------

        if not brand_match:

            return VehicleMatch(
                brand_match=False,
                model_match=False,
                powertrain_match=(
                    powertrain_match
                ),
                confidence=0,
                match_type="NO_MATCH",
            )

        if not model_match:

            return VehicleMatch(
                brand_match=True,
                model_match=False,
                powertrain_match=(
                    powertrain_match
                ),
                confidence=0,
                match_type="NO_MATCH",
            )

        # ------------------------------------------------
        # MODEL MATCH + POWERTRAIN MISMATCH
        # ------------------------------------------------

        if not powertrain_match:

            return VehicleMatch(
                brand_match=True,
                model_match=True,
                powertrain_match=False,
                confidence=80,
                match_type=(
                    "MODEL_MATCH_POWERTRAIN_MISMATCH"
                ),
            )

        # ------------------------------------------------
        # EXACT MATCH
        # ------------------------------------------------

        return VehicleMatch(
            brand_match=True,
            model_match=True,
            powertrain_match=True,
            confidence=100,
            match_type="EXACT_MATCH",
        )