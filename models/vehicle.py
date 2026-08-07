from dataclasses import dataclass


@dataclass
class Vehicle:
    provider: str
    brand: str
    model: str
    trim: str
    fuel_type: str
    monthly_fee: int
    duration: int
    mileage: int
    url: str