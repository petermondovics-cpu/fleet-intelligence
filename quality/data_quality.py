from dataclasses import dataclass
from typing import List


@dataclass
class QualityIssue:
    field: str
    severity: str
    message: str


@dataclass
class QualityResult:
    valid: bool
    confidence: int
    issues: List[QualityIssue]


class DataQualityChecker:

    def check_offer(self, offer) -> QualityResult:

        issues = []

        self._check_basic_fields(
            offer,
            issues,
        )

        self._check_fuel_type(
            offer,
            issues,
        )

        self._check_model_powertrain(
            offer,
            issues,
        )

        if any(
            issue.severity == "ERROR"
            for issue in issues
        ):
            valid = False
            confidence = 0

        elif any(
            issue.severity == "WARNING"
            for issue in issues
        ):
            valid = True
            confidence = 80

        else:
            valid = True
            confidence = 100

        return QualityResult(
            valid=valid,
            confidence=confidence,
            issues=issues,
        )

    def _check_basic_fields(
        self,
        offer,
        issues,
    ):

        required = {
            "provider": offer.provider,
            "brand": offer.brand,
            "model": offer.model,
            "fuel_type": offer.fuel_type,
            "monthly_fee": offer.monthly_fee,
            "duration": offer.duration,
            "mileage": offer.mileage,
        }

        for field, value in required.items():

            if value is None or value == "":

                issues.append(
                    QualityIssue(
                        field=field,
                        severity="ERROR",
                        message=(
                            f"Missing value: {field}"
                        ),
                    )
                )

    def _check_fuel_type(
        self,
        offer,
        issues,
    ):

        valid_fuels = {
            "PETROL",
            "BENZIN",
            "DIESEL",
            "DÍZEL",
            "HYBRID",
            "HIBRID",
            "PHEV",
            "EV",
        }

        fuel = (
            str(offer.fuel_type)
            .strip()
            .upper()
        )

        if fuel not in valid_fuels:

            issues.append(
                QualityIssue(
                    field="fuel_type",
                    severity="WARNING",
                    message=(
                        f"Unknown fuel type: "
                        f"{offer.fuel_type}"
                    ),
                )
            )

    def _check_model_powertrain(
        self,
        offer,
        issues,
    ):

        raw_title = (
            getattr(
                offer,
                "raw_title",
                None,
            )
            or ""
        )

        model_text = (
            f"{offer.brand} "
            f"{offer.model} "
            f"{offer.trim}"
        )

        # A raw title is preferable because the
        # normalizer may have removed technical
        # information such as battery capacity.
        text = (
            raw_title
            if raw_title.strip()
            else model_text
        ).upper()

        fuel = (
            str(offer.fuel_type)
            .strip()
            .upper()
        )

        # ------------------------------------------------
        # EV indicators
        # ------------------------------------------------

        ev_indicators = [
            "KWH",
            "FULL ELECTRIC",
            "FULL-ELECTRIC",
            "ELECTRIC",
            "ELEKTROMOS",
            "E-DRIVE",
            "EDRIVE",
        ]

        has_ev_indicator = any(
            indicator in text
            for indicator in ev_indicators
        )

        # ------------------------------------------------
        # PHEV indicators
        # ------------------------------------------------

        phev_indicators = [
            "PHEV",
            "PLUG-IN",
            "PLUG IN",
            "PLUG-IN HYBRID",
            "PLUG IN HYBRID",
            "DM-I",
            "DM-I",
        ]

        has_phev_indicator = any(
            indicator in text
            for indicator in phev_indicators
        )

        # ------------------------------------------------
        # Explicit fuel indicators
        # ------------------------------------------------

        diesel_indicators = [
            "DIESEL",
            "DÍZEL",
            "BLUE DCI",
            "DCI",
            "TDI",
            "HDI",
        ]

        petrol_indicators = [
            "BENZIN",
            "PETROL",
            "TURBO",
            "TSI",
            "TCE",
            "PURETECH",
        ]

        has_diesel_indicator = any(
            indicator in text
            for indicator in diesel_indicators
        )

        has_petrol_indicator = any(
            indicator in text
            for indicator in petrol_indicators
        )

        # ------------------------------------------------
        # EV vs PHEV conflict
        # ------------------------------------------------

        if (
            has_ev_indicator
            and fuel == "PHEV"
            and not has_phev_indicator
        ):

            issues.append(
                QualityIssue(
                    field="fuel_type",
                    severity="WARNING",
                    message=(
                        "Possible powertrain "
                        "classification conflict: "
                        "raw vehicle title contains "
                        "EV indicators but fuel type "
                        "is PHEV."
                    ),
                )
            )

        # ------------------------------------------------
        # PHEV vs EV conflict
        # ------------------------------------------------

        if (
            has_phev_indicator
            and fuel == "EV"
        ):

            issues.append(
                QualityIssue(
                    field="fuel_type",
                    severity="WARNING",
                    message=(
                        "Possible powertrain "
                        "classification conflict: "
                        "raw vehicle title contains "
                        "PHEV indicators but fuel type "
                        "is EV."
                    ),
                )
            )

        # ------------------------------------------------
        # Diesel vs EV/PHEV conflict
        # ------------------------------------------------

        if (
            has_diesel_indicator
            and fuel in {"EV", "PHEV"}
        ):

            issues.append(
                QualityIssue(
                    field="fuel_type",
                    severity="WARNING",
                    message=(
                        "Possible powertrain "
                        "classification conflict: "
                        "raw vehicle title contains "
                        "diesel indicators but fuel "
                        f"type is {fuel}."
                    ),
                )
            )

        # ------------------------------------------------
        # Petrol vs EV conflict
        # ------------------------------------------------

        if (
            has_petrol_indicator
            and fuel == "EV"
            and not has_ev_indicator
        ):

            issues.append(
                QualityIssue(
                    field="fuel_type",
                    severity="WARNING",
                    message=(
                        "Possible powertrain "
                        "classification conflict: "
                        "raw vehicle title contains "
                        "petrol indicators but fuel "
                        "type is EV."
                    ),
                )
            )