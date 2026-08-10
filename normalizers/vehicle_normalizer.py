import re


class VehicleNormalizer:

    BRANDS = [
        "BYD",
        "PEUGEOT",
        "OPEL",
        "RENAULT",
        "SUZUKI",
    ]

    def normalize(self, title: str) -> dict:

        title = title.upper().strip()

        brand = ""

        for b in self.BRANDS:
            if title.startswith(b):
                brand = b
                break

        model = title

        if brand:
            model = title[len(brand):].strip()

        return {
            "brand": brand,
            "model": model,
        }