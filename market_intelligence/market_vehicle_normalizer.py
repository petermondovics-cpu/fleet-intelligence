from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from models.offer import Offer
from models.vehicle_identity_normalizer import VehicleIdentityNormalizer

IDENTITY_OBSERVED = "OBSERVED"
IDENTITY_INFERRED = "INFERRED"
IDENTITY_UNRESOLVED = "UNRESOLVED"

@dataclass(frozen=True)
class NormalizedMarketOffer:
    provider: str
    brand: Optional[str]
    model: Optional[str]
    trim: Optional[str]
    fuel_type: Optional[str]
    monthly_fee: int
    duration: int
    mileage: int
    url: str
    raw_title: Optional[str]
    identity_status: str
    identity_method: str

class MarketVehicleNormalizer:
    MULTIWORD_BRANDS = (
        "Alfa Romeo", "Aston Martin", "DS Automobiles",
        "Land Rover", "Mercedes-Benz", "Rolls-Royce",
    )

    def __init__(self):
        self.identity = VehicleIdentityNormalizer()

    def normalize(self, offer: Offer) -> NormalizedMarketOffer:
        raw_title = (offer.raw_title or offer.model or "").strip()
        explicit_brand = (offer.brand or "").strip()

        if explicit_brand:
            brand = explicit_brand
            identity_status = IDENTITY_OBSERVED
            identity_method = "PROVIDER_FIELD"
        else:
            brand = self._infer_brand(raw_title, offer.url)
            if brand:
                identity_status = IDENTITY_INFERRED
                identity_method = "TITLE_OR_URL_INFERENCE"
            else:
                identity_status = IDENTITY_UNRESOLVED
                identity_method = "UNRESOLVED"

        model_input = self._strip_brand_prefix(
            raw_title or (offer.model or ""),
            brand,
        )
        trim_input = (offer.trim or "").strip()
        fuel_input = (offer.fuel_type or "").strip()

        canonical_brand = brand or None
        canonical_model = model_input.strip() or None
        canonical_trim = trim_input or None
        canonical_fuel = fuel_input or None

        if brand and canonical_model:
            try:
                n = self.identity.normalize(
                    brand,
                    canonical_model,
                    trim_input,
                    fuel_input,
                )
                canonical_brand = getattr(n, "brand", None) or canonical_brand
                canonical_model = getattr(n, "model", None) or canonical_model
                canonical_fuel = getattr(n, "fuel_type", None) or canonical_fuel
                normalized_trim = getattr(n, "trim", None)
                if normalized_trim:
                    canonical_trim = normalized_trim
            except Exception:
                pass

        return NormalizedMarketOffer(
            provider=offer.provider,
            brand=canonical_brand,
            model=canonical_model,
            trim=canonical_trim,
            fuel_type=canonical_fuel,
            monthly_fee=offer.monthly_fee,
            duration=offer.duration,
            mileage=offer.mileage,
            url=offer.url,
            raw_title=raw_title or None,
            identity_status=identity_status,
            identity_method=identity_method,
        )

    def _infer_brand(self, title: str, url: str) -> Optional[str]:
        title_cf = title.casefold()
        for brand in self.MULTIWORD_BRANDS:
            if title_cf.startswith(brand.casefold() + " "):
                return brand

        if title:
            first = title.split()[0].strip(" -–—|/")
            if first and any(ch.isalpha() for ch in first):
                return first

        try:
            parts = [p for p in urlparse(url).path.split("/") if p]
        except Exception:
            parts = []

        provider = (url or "").casefold()
        if "ayvens" in provider and parts:
            return self._slug_to_brand(parts[0])

        if "arval" in provider:
            try:
                marker = parts.index("tartos-berleti-ajantlat")
                slug = parts[marker + 1]
                return self._slug_to_brand(slug.split("-")[0])
            except Exception:
                pass

        return None

    @staticmethod
    def _slug_to_brand(value: str) -> Optional[str]:
        cleaned = (value or "").replace("_", "-").strip("- ")
        if not cleaned:
            return None
        return " ".join(part.capitalize() for part in cleaned.split("-") if part)

    @staticmethod
    def _strip_brand_prefix(title: str, brand: Optional[str]) -> str:
        text = (title or "").strip()
        if not brand:
            return text
        if text.casefold().startswith(brand.casefold()):
            return text[len(brand):].lstrip(" -–—|/")
        return text
