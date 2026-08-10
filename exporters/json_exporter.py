import json
from dataclasses import asdict
from pathlib import Path

from models.offer import Offer


class JsonExporter:

    def export(self, offers: list[Offer], filename: str) -> None:

        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        filepath = output_dir / filename

        data = [asdict(offer) for offer in offers]

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False,
            )

        print(f"\n✅ JSON exported to {filepath}")