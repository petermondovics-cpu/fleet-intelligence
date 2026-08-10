from openpyxl import Workbook
from models.offer import Offer
from pathlib import Path


class ExcelExporter:

    def export(self, offers: list[Offer], filename: str):

        wb = Workbook()
        ws = wb.active
        ws.title = "Offers"

        ws.append([
            "Provider",
            "Brand",
            "Model",
            "Trim",
            "Fuel",
            "Monthly fee",
            "Duration",
            "Mileage",
            "URL",
        ])

        for offer in offers:

            ws.append([
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

        wb.save(f"output/{filename}")

        print(f"✅ Excel exported: output/{filename}")