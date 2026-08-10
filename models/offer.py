from dataclasses import dataclass, field
from datetime import datetime

from models.provider import Provider
from models.vehicle import Vehicle


@dataclass(slots=True)
class Offer:
    """
    Leasing offer for a specific vehicle from a specific provider.
    """

    provider: Provider

    vehicle: Vehicle

    monthly_fee: int

    duration: int

    mileage: int

    deposit: int = 0

    availability: str = ""

    url: str = ""

    source: str = ""

    scraped_at: datetime = field(default_factory=datetime.utcnow)