from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Vehicle:
    """
    Canonical vehicle definition.

    This object represents a vehicle independently
    from any leasing provider.
    """

    brand: str
    model: str

    trim: str = ""

    body_type: Optional[str] = None

    fuel_type: Optional[str] = None

    gearbox: Optional[str] = None

    drive: Optional[str] = None

    horsepower: Optional[int] = None

    battery_kwh: Optional[float] = None

    electric_range_km: Optional[int] = None