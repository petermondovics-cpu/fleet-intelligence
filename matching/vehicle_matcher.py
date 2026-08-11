import re
from dataclasses import dataclass
from typing import List


@dataclass
class VehicleMatch:
    brand_match: bool
    model_match: bool
    powertrain_match: bool

    confidence: int

    match_type: str


class VehicleMatcher:

    BRAND_ALIASES = {
        "SKODA": "SKODA",
        "ŠKODA": "SKODA",
        "MERCEDES": "MERCEDES-BENZ",
        "MERCEDES-BENZ": "MERCEDES-BENZ",
    }

    MODEL_ALIASES = {
        "COMBO CARGO": "COMBO",
        "COMBO": "COMBO",

        "RANGE ROVER SPORT": "RANGE ROVER SPORT",
        "RANGE ROVER VELAR": "RANGE ROVER VELAR",

        "S-CROSS": "S-CROSS",
        "SCROSS": "S-CROSS",
    }

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
            self._normalize_brand(brand_a)
        )

        normalized_brand_b = (
            self._normalize_brand(brand_b)
        )

        normalized_model_a = (
            self._normalize_model(model_a)
        )

        normalized_model_b = (
            self._normalize_model(model_b)
        )

        normalized_fuel_a = (
            self._normalize_fuel(fuel_a)
        )

        normalized_fuel_b = (
            self._normalize_fuel(fuel_b)
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

        confidence = 0

        if brand_match:
            confidence += 30

        if model_match:
            confidence += 50

        if powertrain_match:
            confidence += 20

        if not brand_match:
            confidence = 0
            match_type = "NO_MATCH"

        elif not model_match:
            confidence = 0
            match_type = "NO_MATCH"

        elif not powertrain_match:
            confidence = 80
            match_type = "MODEL_MATCH_POWERTRAIN_MISMATCH"

        elif confidence == 100:
            match_type = "EXACT_MATCH"

        else:
            match_type = "PARTIAL_MATCH"

        return VehicleMatch(
            brand_match=brand_match,
            model_match=model_match,
            powertrain_match=powertrain_match,
            confidence=confidence,
            match_type=match_type,
        )

    def _normalize_brand(
        self,
        brand: str,
    ) -> str:

        value = self._clean(brand)

        return self.BRAND_ALIASES.get(
            value,
            value,
        )

    def _normalize_model(
        self,
        model: str,
    ) -> str:

        value = self._clean(model)

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return self.MODEL_ALIASES.get(
            value,
            value,
        )

    def _normalize_fuel(
        self,
        fuel: str,
    ) -> str:

        value = self._clean(fuel)

        aliases = {
            "BENZIN": "PETROL",
            "PETROL": "PETROL",

            "DÍZEL": "DIESEL",
            "DIZEL": "DIESEL",
            "DIESEL": "DIESEL",

            "HIBRID": "HYBRID",
            "HYBRID": "HYBRID",

            "PHEV": "PHEV",

            "EV": "EV",
            "ELEKTROMOS": "EV",
        }

        return aliases.get(
            value,
            value,
        )

    def _clean(
        self,
        value: str,
    ) -> str:

        if not value:
            return ""

        return (
            value
            .strip()
            .upper()
        )