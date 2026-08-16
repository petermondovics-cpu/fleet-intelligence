from pathlib import Path

PATH = Path("market_intelligence/benchmark_decision_dashboard_service_v2.py")
BACKUP = Path(
    "market_intelligence/"
    "benchmark_decision_dashboard_service_v2.py.pre_v2_2_result_serialization.bak"
)

OLD = """            results=tuple(asdict(row) for row in results),
"""
NEW = """            results=tuple(
                self._serialize_record(row)
                for row in results
            ),
"""

def main():
    text = PATH.read_text(encoding="utf-8")

    if "self._serialize_record(row)" in text:
        print("Already patched to V2.2.")
        return

    if OLD not in text:
        raise SystemExit(
            "Result serialization anchor not found; refusing unsafe patch."
        )

    if "def _serialize_record(" not in text:
        raise SystemExit(
            "V2.1 serialization helper is missing. Apply V2.1 first."
        )

    if not BACKUP.exists():
        BACKUP.write_text(text, encoding="utf-8")
        print("Backup:", BACKUP)

    text = text.replace(OLD, NEW, 1)

    compile(text, str(PATH), "exec")
    PATH.write_text(text, encoding="utf-8")

    print("Patched:", PATH)
    print("Benchmark Decision Dashboard V2.2 result serialization fix: INSTALLED")

if __name__ == "__main__":
    main()
