from dataclasses import dataclass
from datetime import datetime

@dataclass
class Offer:
    provider: str
    brand: str
    model: str
    trim: str
    fuel_type: str
    monthly_fee: int
    duration: int
    mileage: int
    url: str