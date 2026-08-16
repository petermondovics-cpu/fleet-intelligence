import re


class VehicleNormalizer:

    # ------------------------------------------------
    # BRANDS
    # ------------------------------------------------

    BRANDS = [
        "MERCEDES-BENZ",
        "LAND ROVER",
        "PEUGEOT",
        "VOLKSWAGEN",
        "HYUNDAI",
        "RENAULT",
        "TOYOTA",
        "NISSAN",
        "SUZUKI",
        "CITROEN",
        "SKODA",
        "ŠKODA",
        "MAXUS",
        "OMODA",
        "JAECOO",
        "LEXUS",
        "DACIA",
        "MERCEDES",
        "BMW",
        "VOLVO",
        "KIA",
        "FORD",
        "OPEL",
        "BYD",
        "AUDI",
        "FIAT",
        "MG",
        "HONDA",
        "MAZDA",
        "MITSUBISHI",
        "SUBARU",
    ]

    BRAND_ALIASES = {
        "ŠKODA": "SKODA",
        "SKODA": "SKODA",
        "MERCEDES": "MERCEDES-BENZ",
    }

    # ------------------------------------------------
    # MODEL PATTERNS
    # ------------------------------------------------

    MODEL_PATTERNS = {

        "BYD": [
            "ATTO 2",
            "ATTO 3",
            "ATTO 4",
            "SEALION 5",
            "SEALION 7",
            "SEAL U",
            "SEAL",
            "DOLPHIN",
            "HAN",
            "TANG",
        ],

        "PEUGEOT": [
            "208",
            "2008",
            "308",
            "408",
            "3008",
            "5008",
            "PARTNER",
            "EXPERT",
        ],

        "OPEL": [
            "COMBO CARGO",
            "COMBO",
            "CORSA",
            "MOKKA",
            "ASTRA",
            "FRONTERA",
            "GRANDLAND",
            "MOVANO",
            "VIVARO",
            "ZAFIRA",
        ],

        "RENAULT": [
            "CLIO",
            "CAPTUR",
            "MEGANE",
            "AUSTRAL",
            "ARKANA",
            "KANGOO",
            "TRAFIC",
            "MASTER",
        ],

        "SUZUKI": [
            "SWIFT",
            "VITARA",
            "S-CROSS",
            "ACROSS",
            "IGNIS",
        ],

        "KIA": [
            "PICANTO",
            "RIO",
            "CEED",
            "NIRO",
            "SPORTAGE",
            "SORENTO",
            "PV5",
            "EV3",
            "EV6",
            "EV9",
            "K4",
            "XCEED",
        ],

        "TOYOTA": [
            "YARIS CROSS",
            "YARIS",
            "COROLLA",
            "CAMRY",
            "C-HR",
            "RAV4",
            "PROACE MAX",
            "PROACE CITY",
        ],

        "VOLVO": [
            "EX30",
            "EX60",
            "XC40",
            "XC60",
            "XC90",
        ],

        "BMW": [
            "IX1",
            "I4",
            "X3",
        ],

        "FORD": [
            "KUGA",
            "RANGER",
            "TRANSIT CUSTOM",
            "TRANSIT",
        ],

        "HYUNDAI": [
            "I20",
            "I30 WAGON",
            "KONA",
            "TUCSON",
            "INSTER",
        ],

        "NISSAN": [
            "QASHQAI",
            "ARIYA",
            "X-TRAIL",
        ],

        "MERCEDES-BENZ": [
            "C-OSZTÁLY",
            "GLA",
            "CLA",
            "SPRINTER",
        ],

        "LAND ROVER": [
            "DEFENDER",
            "RANGE ROVER SPORT",
            "RANGE ROVER VELAR",
            "RANGE ROVER",
        ],

        "LEXUS": [
            "RZ",
            "NX",
            "LBX",
        ],

        "SKODA": [
            "SUPERB COMBI",
            "ELROQ",
            "OCTAVIA COMBI",
            "KODIAQ",
            "OCTAVIA",
            "SUPERB",
        ],

        "MAXUS": [
            "T60 MAX",
        ],

        "OMODA": [
            "9",
        ],

        "DACIA": [
            "DUSTER",
        ],
    }

    # ------------------------------------------------
    # MODEL ALIASES
    # ------------------------------------------------

    MODEL_ALIASES = {

        "COMBO CARGO": "COMBO",
        "COMBO": "COMBO",

        "SCROSS": "S-CROSS",
        "S-CROSS": "S-CROSS",

    }

    # ------------------------------------------------
    # FUEL ALIASES
    # ------------------------------------------------

    FUEL_ALIASES = {

        "EV": "EV",
        "ELEKTROMOS": "EV",
        "100% ELEKTROMOS": "EV",

        "PHEV": "PHEV",
        "PLUG-IN HIBRID": "PHEV",
        "PLUG IN HIBRID": "PHEV",

        "HYBRID": "HYBRID",
        "HIBRID": "HYBRID",
        "BENZIN MILD-HIBRID": "HYBRID",
        "DÍZEL MILD-HIBRID": "HYBRID",

        "PETROL": "PETROL",
        "BENZIN": "PETROL",

        "DIESEL": "DIESEL",
        "DÍZEL": "DIESEL",
        "DIZEL": "DIESEL",
    }

    # ------------------------------------------------
    # NORMALIZE
    # ------------------------------------------------

    def normalize(
        self,
        title: str,
        fuel_type: str = "",
    ) -> dict:

        original_title = title

        title = self._clean(
            title
        )

        brand = self._extract_brand(
            title
        )

        model = self._extract_model(
            title,
            brand,
        )

        fuel_type = (
            self.normalize_fuel_type(
                fuel_type
            )
        )

        return {
            "original_title": original_title,
            "brand": brand,
            "model": model,
            "fuel_type": fuel_type,
        }

    # ------------------------------------------------
    # FUEL
    # ------------------------------------------------

    def normalize_fuel_type(
        self,
        fuel_type: str,
    ) -> str:

        if not fuel_type:
            return ""

        normalized = (
            fuel_type
            .upper()
            .strip()
        )

        return self.FUEL_ALIASES.get(
            normalized,
            normalized,
        )

    # ------------------------------------------------
    # MODEL
    # ------------------------------------------------

    def normalize_model(
        self,
        model: str,
    ) -> str:

        if not model:
            return ""

        normalized = self._clean(
            model
        )

        normalized = (
            self.MODEL_ALIASES.get(
                normalized,
                normalized,
            )
        )

        return normalized

    # ------------------------------------------------
    # BRAND
    # ------------------------------------------------

    def normalize_brand(
        self,
        brand: str,
    ) -> str:

        if not brand:
            return ""

        normalized = self._clean(
            brand
        )

        return self.BRAND_ALIASES.get(
            normalized,
            normalized,
        )

    # ------------------------------------------------
    # VEHICLE KEY
    #
    # Fontos:
    # COMBO CARGO -> COMBO
    # SCROSS -> S-CROSS
    # ------------------------------------------------

    def vehicle_key(
        self,
        brand: str,
        model: str,
        fuel_type: str,
    ) -> str:

        brand = self.normalize_brand(
            brand
        )

        model = self.normalize_model(
            model
        )

        fuel_type = (
            self.normalize_fuel_type(
                fuel_type
            )
        )

        return (
            f"{brand}|"
            f"{model}|"
            f"{fuel_type}"
        )

    # ------------------------------------------------
    # CLEAN
    # ------------------------------------------------

    def _clean(
        self,
        value: str,
    ) -> str:

        if not value:
            return ""

        value = (
            value
            .upper()
            .strip()
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value

    # ------------------------------------------------
    # BRAND EXTRACTION
    # ------------------------------------------------

    def _extract_brand(
        self,
        title: str,
    ) -> str:

        for brand in sorted(
            self.BRANDS,
            key=len,
            reverse=True,
        ):

            if title.startswith(
                brand
            ):

                return self.BRAND_ALIASES.get(
                    brand,
                    brand,
                )

        return ""

    # ------------------------------------------------
    # MODEL EXTRACTION
    # ------------------------------------------------

    def _extract_model(
        self,
        title: str,
        brand: str,
    ) -> str:

        if not brand:
            return title

        remaining = title

        # ------------------------------------------------
        # Remove source brand from title.
        # Handles aliases such as:
        #
        # ŠKODA -> SKODA
        # MERCEDES -> MERCEDES-BENZ
        # ------------------------------------------------

        for source_brand in sorted(
            self.BRANDS,
            key=len,
            reverse=True,
        ):

            normalized_brand = (
                self.BRAND_ALIASES.get(
                    source_brand,
                    source_brand,
                )
            )

            if (
                normalized_brand == brand
                and
                remaining.startswith(
                    source_brand
                )
            ):

                remaining = (
                    remaining[
                        len(source_brand):
                    ].strip()
                )

                break

        patterns = self.MODEL_PATTERNS.get(
            brand,
            [],
        )

        for pattern in sorted(
            patterns,
            key=len,
            reverse=True,
        ):

            if remaining.startswith(
                pattern
            ):

                return self.normalize_model(
                    pattern
                )

        # ------------------------------------------------
        # FALLBACK
        # ------------------------------------------------

        parts = remaining.split()

        if len(parts) >= 2:

            return self.normalize_model(
                " ".join(parts[:2])
            )

        return self.normalize_model(
            remaining
        )