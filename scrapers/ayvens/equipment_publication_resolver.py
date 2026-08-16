from dataclasses import dataclass
from typing import Optional


PROVIDER_EQUIPMENT_NOT_PUBLISHED = "NOT_PUBLISHED"
PROVIDER_EQUIPMENT_PUBLISHED = "PUBLISHED"
PROVIDER_EQUIPMENT_UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class AyvensEquipmentPublicationResolution:
    status: str
    source_url: str
    standard_count: Optional[int]
    optional_count: Optional[int]
    diagnostic: str


class AyvensEquipmentPublicationResolver:
    """
    Ayvens Equipment Publication Resolver V1.

    Uses the exact-offer Ayvens API only to decide whether the provider
    actually publishes equipment lists for the current offer.

    IMPORTANT semantics:
    - basic_config=[] / extra_config=[] means the provider does not publish
      list items for those dimensions in the exact-offer API.
    - This NEVER means the vehicle has zero standard/optional equipment.
    - Non-empty lists mean provider publication exists and manufacturer
      fallback must not replace it.
    - Missing keys / failed API / identity mismatch remain UNRESOLVED.
    """

    API_ROOT = (
        "https://autotartosberlet.ayvens.com/api/cars"
    )

    def resolve(
        self,
        page,
        offer,
    ) -> AyvensEquipmentPublicationResolution:

        api_url = self._api_url_from_offer(
            getattr(offer, "url", "")
            or getattr(page, "url", "")
        )

        if not api_url:
            return self._unresolved(
                "",
                "Could not derive exact-offer Ayvens API URL.",
            )

        try:
            response = page.request.get(
                api_url,
                timeout=60000,
            )
        except Exception as exc:
            return self._unresolved(
                api_url,
                f"Ayvens exact-offer API request failed: {exc}",
            )

        if not response.ok:
            return self._unresolved(
                api_url,
                f"Ayvens exact-offer API returned HTTP {response.status}.",
            )

        try:
            payload = response.json()
        except Exception as exc:
            return self._unresolved(
                api_url,
                f"Ayvens exact-offer API JSON parsing failed: {exc}",
            )

        data = (
            payload.get("data")
            if isinstance(payload, dict)
            else None
        )

        if not isinstance(data, dict):
            return self._unresolved(
                api_url,
                "Ayvens exact-offer API does not contain a data object.",
            )

        if not self._identity_matches(
            data,
            offer,
        ):
            return self._unresolved(
                api_url,
                "Ayvens exact-offer API identity does not match the loaded offer.",
            )

        if (
            "basic_config" not in data
            or "extra_config" not in data
        ):
            return self._unresolved(
                api_url,
                "Ayvens exact-offer API does not expose both equipment publication fields.",
            )

        basic = data.get("basic_config")
        extra = data.get("extra_config")

        if not isinstance(basic, list) or not isinstance(extra, list):
            return self._unresolved(
                api_url,
                "Ayvens equipment publication fields are not lists.",
            )

        if basic or extra:
            return AyvensEquipmentPublicationResolution(
                status=PROVIDER_EQUIPMENT_PUBLISHED,
                source_url=api_url,
                standard_count=len(basic),
                optional_count=len(extra),
                diagnostic=(
                    "Ayvens exact-offer API publishes one or more equipment "
                    "items. Provider evidence must remain primary."
                ),
            )

        return AyvensEquipmentPublicationResolution(
            status=PROVIDER_EQUIPMENT_NOT_PUBLISHED,
            source_url=api_url,
            standard_count=0,
            optional_count=0,
            diagnostic=(
                "Ayvens exact-offer API explicitly exposes basic_config=[] "
                "and extra_config=[]. This is classified as provider list "
                "NOT_PUBLISHED, not as zero vehicle equipment."
            ),
        )

    @classmethod
    def _api_url_from_offer(
        cls,
        url: str,
    ) -> Optional[str]:

        if not url:
            return None

        marker = (
            "autotartosberlet.ayvens.com/"
        )

        if marker not in url:
            return None

        path = (
            url.split(marker, 1)[1]
            .split("?", 1)[0]
            .split("#", 1)[0]
            .strip("/")
        )

        parts = [
            p
            for p in path.split("/")
            if p
        ]

        if len(parts) != 2:
            return None

        return (
            f"{cls.API_ROOT}/"
            f"{parts[0]}/{parts[1]}"
        )

    @staticmethod
    def _identity_matches(
        data: dict,
        offer,
    ) -> bool:

        brand = data.get("brand")

        api_brand = (
            brand.get("name")
            if isinstance(brand, dict)
            else None
        )

        api_model = (
            (data.get("model") or {})
            .get("name")
            if isinstance(
                data.get("model"),
                dict,
            )
            else None
        )

        api_trim = data.get(
            "configuration"
        )

        api_fuel = data.get(
            "fuel_type"
        )

        target_brand = (
            getattr(offer, "brand", "")
            or ""
        )
        target_model = (
            getattr(offer, "model", "")
            or ""
        )
        target_trim = (
            getattr(offer, "trim", "")
            or ""
        )
        target_fuel = (
            getattr(offer, "fuel_type", "")
            or ""
        )

        def norm(value):
            return (
                str(value or "")
                .casefold()
                .replace("dm-i", "")
                .replace("dm i", "")
                .replace("-", " ")
                .replace("_", " ")
                .strip()
            )

        if norm(api_brand) != norm(target_brand):
            return False

        if norm(api_model) != norm(target_model):
            return False

        # Exact provider trim wording is available in the API.
        if norm(api_trim) != norm(target_trim):
            return False

        fuel_a = norm(api_fuel)
        fuel_b = norm(target_fuel)

        fuel_compatible = (
            fuel_a == fuel_b
            or (
                "plug in hibrid" in fuel_a
                and fuel_b == "phev"
            )
            or (
                fuel_a == "phev"
                and "plug in hibrid" in fuel_b
            )
        )

        return fuel_compatible

    @staticmethod
    def _unresolved(
        source_url: str,
        diagnostic: str,
    ):
        return AyvensEquipmentPublicationResolution(
            status=PROVIDER_EQUIPMENT_UNRESOLVED,
            source_url=source_url,
            standard_count=None,
            optional_count=None,
            diagnostic=diagnostic,
        )
