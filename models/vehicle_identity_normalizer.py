from dataclasses import dataclass
import re
from typing import Optional


@dataclass(frozen=True)
class CanonicalVehicleIdentity:
    brand: str
    model: str
    fuel_type: str
    raw_brand: str
    raw_model: str
    raw_trim: str


class VehicleIdentityNormalizer:
    """
    Vehicle Identity Normalization V1.

    Purpose:
    Normalize provider-specific model naming WITHOUT changing the
    underlying observed fields.

    Safety rules:
    - raw provider identity is always preserved;
    - normalization is deterministic and rule-based;
    - no fuzzy matching inside this class;
    - powertrain/engine/trim tokens may be removed from the model name;
    - body/model distinctions are preserved unless an explicit rule says
      they are provider naming variants of the same model family.
    """

    def normalize(
        self,
        brand: str,
        model: str,
        trim: str,
        fuel_type: str,
    ) -> CanonicalVehicleIdentity:

        raw_brand = brand.strip()
        raw_model = model.strip()
        raw_trim = trim.strip()

        canonical_brand = self._canonical_brand(
            raw_brand
        )

        canonical_model = (
            self._canonical_model(
                canonical_brand,
                raw_model,
                raw_trim,
            )
        )

        canonical_fuel = (
            self._canonical_fuel(
                fuel_type
            )
        )

        return CanonicalVehicleIdentity(
            brand=canonical_brand,
            model=canonical_model,
            fuel_type=canonical_fuel,
            raw_brand=raw_brand,
            raw_model=raw_model,
            raw_trim=raw_trim,
        )

    # ============================================================
    # BRAND
    # ============================================================

    @staticmethod
    def _canonical_brand(
        brand: str,
    ) -> str:

        value = (
            brand.strip()
            .upper()
        )

        mapping = {
            "MERCEDES BENZ": "MERCEDES-BENZ",
            "MERCEDES-BENZ": "MERCEDES-BENZ",
            "LAND ROVER": "LAND ROVER",
        }

        return mapping.get(
            value,
            value,
        )

    # ============================================================
    # MODEL
    # ============================================================

    def _canonical_model(
        self,
        brand: str,
        model: str,
        trim: str,
    ) -> str:

        value = self._normalize_text(
            model
        )

        # --------------------------------------------------------
        # Explicit provider naming rules learned from live pages
        # --------------------------------------------------------

        if brand == "BYD":

            # ATTO 2 DM-i is the PHEV derivative of ATTO 2.
            if value.startswith(
                "ATTO 2 DM I"
            ):
                return "ATTO 2"

            # Preserve ATTO 3 as a different model.
            if value.startswith(
                "ATTO 3"
            ):
                return "ATTO 3"

            # SEAL U DM-i is the powertrain derivative of SEAL U.
            if value.startswith(
                "SEAL U DM I"
            ):
                return "SEAL U"

            # Arval may append battery / trim text to the parsed model.
            m = re.match(
                r"^(SEALION\s+\d+)",
                value,
            )
            if m:
                return m.group(1)

            m = re.match(
                r"^(ATTO\s+\d+)",
                value,
            )
            if m:
                return m.group(1)

            if value.startswith(
                "SEAL U"
            ):
                return "SEAL U"

        if brand == "VOLVO":

            m = re.match(
                r"^(XC\d+)",
                value,
            )

            if m:
                return m.group(1)

        if brand == "OPEL":

            # Arval: COMBO CARGO
            # Ayvens: Combo / trim "Furgon alap ..."
            #
            # Canonical model family is COMBO. Cargo/furgon remains
            # derivative/body evidence in the raw fields.
            if value.startswith(
                "COMBO CARGO"
            ):
                return "COMBO"

            if value == "COMBO":
                return "COMBO"

            if value.startswith(
                "CORSA"
            ):
                return "CORSA"

            if value.startswith(
                "ASTRA"
            ):
                return "ASTRA"

        if brand == "RENAULT":

            if value.startswith(
                "KANGOO"
            ):
                return "KANGOO"

        if brand == "SUZUKI":

            if (
                value.startswith("S CROSS")
                or value.startswith("SCROSS")
            ):
                return "S-CROSS"

        if brand == "PEUGEOT":

            m = re.match(
                r"^(\d{3,4})\b",
                value,
            )

            if m:
                return m.group(1)

        # --------------------------------------------------------
        # Conservative generic cleanup
        # --------------------------------------------------------

        return value

    # ============================================================
    # FUEL
    # ============================================================

    @staticmethod
    def _canonical_fuel(
        fuel_type: str,
    ) -> str:

        value = (
            fuel_type.strip()
            .casefold()
        )

        mapping = {
            "phev": "PHEV",
            "plug-in hibrid": "PHEV",
            "benzin plug-in hibrid": "PHEV",
            "ev": "EV",
            "elektromos": "EV",
            "diesel": "DIESEL",
            "dízel": "DIESEL",
            "petrol": "PETROL",
            "benzin": "PETROL",
            "hybrid": "HYBRID",
            "hibrid": "HYBRID",
            "benzin mild-hibrid": "MHEV",
            "mild-hibrid": "MHEV",
            "mhev": "MHEV",
        }

        return mapping.get(
            value,
            fuel_type.strip().upper(),
        )

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:

        value = (
            text.strip()
            .upper()
            .replace("DM-I", "DM I")
            .replace("DM–I", "DM I")
            .replace("-", " ")
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

        return value
