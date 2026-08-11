from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Offer:
    """
    Leasing offer collected from a provider.

    This is the current V1-compatible offer model.
    The domain model will be further normalized in a later sprint.
    """

    provider: str

    brand: str

    model: str

    trim: str

    fuel_type: str

    monthly_fee: int

    duration: int

    mileage: int

    url: str

    scraped_at: datetime = None

    source: Optional[str] = None

    raw_title: Optional[str] = None