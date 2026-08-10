from pathlib import Path

from openpyxl import Workbook

from models.offer import Offer


class ExcelExporter:

    def export(self, offers: list[Offer], filename: str):

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Offers"

        worksheet.append([
            "Provider",
            "Brand",
            "Model",
            "Trim",
            "Fuel",
            "Monthly Fee",
            "Duration",
            "Mileage",
            "URL",
        ])

        for offer in offers:
            worksheet.append([
                offer.provider,
                offer.brand,
                offer.model,
                offer.trim,
                offer.fuel_type,
                offer.monthly_fee,
                offer.duration,
                offer.mileage,
                offer.url,
            ])

        Path("output").mkdir(exist_ok=True)

        filepath = Path("output") / filename
        workbook.save(filepath)

        print(f"✅ Excel exported to {filepath}")