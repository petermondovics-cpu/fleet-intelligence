from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Provider:
    """
    Fleet leasing provider.

    Examples:
        - Arval
        - Ayvens
        - Mercarius
        - Porsche Finance
    """

    id: str

    name: str

    website: str

    country: str = "HU"

    currency: str = "HUF"

    language: str = "hu"

    active: bool = True

    logo: Optional[str] = None
    