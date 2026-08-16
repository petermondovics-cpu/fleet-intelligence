import re
from dataclasses import dataclass

from models.offer import Offer


@dataclass
class VehicleVariant:

    variant_key: str

    power_kw: int | None
    power_hp: int | None

    fuel_type: str

    variant_confidence: int

    variant_match_type: str


class VehicleVariantMatcher:

    """
    Vehicle Variant V1.

    A modellazonosítást nem végzi újra.
    A Vehicle Identity V2 eredményére épül.

    Elsődleges variant jelek:

    - teljesítmény kW
    - teljesítmény LE / HP
    - fuel_type

    V1-ben nem próbálunk minden felszereltségi
    szintet intelligensen felismerni.
    """

    # ------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------

    def extract(
        self,
        offer: Offer,
    ) -> VehicleVariant:

        text_parts = [
            offer.trim or "",
            offer.raw_title or "",
            offer.model or "",
        ]

        text = " ".join(
            text_parts
        ).upper()

        power_kw = (
            self._extract_kw(
                text
            )
        )

        power_hp = (
            self._extract_hp(
                text
            )
        )

        # ------------------------------------------------
        # KW -> HP
        #
        # Ha csak kW áll rendelkezésre,
        # hozzávetőleges LE értéket képezünk.
        #
        # 1 kW ≈ 1.35962 LE
        # ------------------------------------------------

        if (
            power_hp is None
            and power_kw is not None
        ):

            power_hp = round(
                power_kw * 1.35962
            )

        fuel_type = (
            self._normalize_fuel(
                offer.fuel_type
            )
        )

        # ------------------------------------------------
        # VARIANT KEY
        # ------------------------------------------------

        key_parts = []

        if fuel_type:

            key_parts.append(
                fuel_type
            )

        if power_hp is not None:

            key_parts.append(
                f"{power_hp}HP"
            )

        elif power_kw is not None:

            key_parts.append(
                f"{power_kw}KW"
            )

        # ------------------------------------------------
        # NO VARIANT INFORMATION
        # ------------------------------------------------

        if not key_parts:

            return VehicleVariant(

                variant_key="UNKNOWN",

                power_kw=None,

                power_hp=None,

                fuel_type=fuel_type,

                variant_confidence=0,

                variant_match_type=(
                    "NO_VARIANT_INFORMATION"
                ),
            )

        # ------------------------------------------------
        # CONFIDENCE
        # ------------------------------------------------

        if (
            power_hp is not None
            and fuel_type
        ):

            confidence = 100

            match_type = (
                "EXACT_VARIANT"
            )

        elif power_hp is not None:

            confidence = 90

            match_type = (
                "POWER_VARIANT"
            )

        elif fuel_type:

            confidence = 80

            match_type = (
                "POWERTRAIN_VARIANT"
            )

        else:

            confidence = 0

            match_type = (
                "NO_VARIANT_INFORMATION"
            )

        return VehicleVariant(

            variant_key=(
                "|".join(key_parts)
            ),

            power_kw=power_kw,

            power_hp=power_hp,

            fuel_type=fuel_type,

            variant_confidence=confidence,

            variant_match_type=match_type,
        )

    # ------------------------------------------------
    # MATCH
    # ------------------------------------------------

    def match(
        self,
        offer_a: Offer,
        offer_b: Offer,
    ) -> VehicleVariant:

        variant_a = self.extract(
            offer_a
        )

        variant_b = self.extract(
            offer_b
        )

        # ------------------------------------------------
        # EXACT VARIANT
        # ------------------------------------------------

        if (
            variant_a.variant_key
            == variant_b.variant_key
        ):

            return VehicleVariant(

                variant_key=(
                    variant_a.variant_key
                ),

                power_kw=(
                    variant_a.power_kw
                    if variant_a.power_kw
                    is not None
                    else variant_b.power_kw
                ),

                power_hp=(
                    variant_a.power_hp
                    if variant_a.power_hp
                    is not None
                    else variant_b.power_hp
                ),

                fuel_type=(
                    variant_a.fuel_type
                ),

                variant_confidence=min(
                    variant_a.variant_confidence,
                    variant_b.variant_confidence,
                ),

                variant_match_type=(
                    "EXACT_VARIANT"
                ),
            )

        # ------------------------------------------------
        # POWERTRAIN MISMATCH
        # ------------------------------------------------

        if (
            variant_a.fuel_type
            and variant_b.fuel_type
            and
            variant_a.fuel_type
            != variant_b.fuel_type
        ):

            return VehicleVariant(

                variant_key="",

                power_kw=None,

                power_hp=None,

                fuel_type="",

                variant_confidence=0,

                variant_match_type=(
                    "VARIANT_POWERTRAIN_MISMATCH"
                ),
            )

        # ------------------------------------------------
        # POWER MISMATCH
        # ------------------------------------------------

        if (
            variant_a.power_hp is not None
            and variant_b.power_hp is not None
            and
            variant_a.power_hp
            != variant_b.power_hp
        ):

            return VehicleVariant(

                variant_key="",

                power_kw=None,

                power_hp=None,

                fuel_type=(
                    variant_a.fuel_type
                ),

                variant_confidence=0,

                variant_match_type=(
                    "VARIANT_POWER_MISMATCH"
                ),
            )

        # ------------------------------------------------
        # UNKNOWN / PARTIAL
        # ------------------------------------------------

        return VehicleVariant(

            variant_key="",

            power_kw=None,

            power_hp=None,

            fuel_type=(
                variant_a.fuel_type
                or variant_b.fuel_type
            ),

            variant_confidence=50,

            variant_match_type=(
                "VARIANT_PARTIAL_MATCH"
            ),
        )

    # ------------------------------------------------
    # POWER EXTRACTION
    # ------------------------------------------------

    def _extract_kw(
        self,
        text: str,
    ) -> int | None:

        patterns = [

            r"\(\s*(\d{2,3})\s*KW",

            r"\b(\d{2,3})\s*KW\b",

        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
            )

            if match:

                return int(
                    match.group(1)
                )

        return None

    # ------------------------------------------------
    # HP EXTRACTION
    # ------------------------------------------------

    def _extract_hp(
        self,
        text: str,
    ) -> int | None:

        patterns = [

            r"(\d{2,3})\s*LE\b",

            r"(\d{2,3})\s*HP\b",

        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
            )

            if match:

                return int(
                    match.group(1)
                )

        return None

    # ------------------------------------------------
    # FUEL NORMALIZATION
    # ------------------------------------------------

    def _normalize_fuel(
        self,
        fuel_type: str,
    ) -> str:

        value = (
            fuel_type
            .upper()
            .strip()
        )

        aliases = {

            "DÍZEL": "DIESEL",
            "DIZEL": "DIESEL",

            "BENZIN": "PETROL",

            "ELEKTROMOS": "EV",

            "PLUG-IN HIBRID": "PHEV",
            "PLUG IN HIBRID": "PHEV",

            "HIBRID": "HYBRID",
        }

        return aliases.get(
            value,
            value,
        )