from pathlib import Path

PATH = Path("market_intelligence/benchmark_decision_dashboard_service_v2.py")
BACKUP = Path(
    "market_intelligence/"
    "benchmark_decision_dashboard_service_v2.py.pre_v2_1_run_serialization.bak"
)

OLD = """            run=asdict(run) if run is not None else None,
"""
NEW = """            run=self._serialize_record(run),
"""

HELPER_ANCHOR = """    @staticmethod
    def _decision(response):
"""
HELPER = """    @staticmethod
    def _serialize_record(record):
        if record is None:
            return None

        try:
            return asdict(record)
        except TypeError:
            data = getattr(record, "__dict__", None)
            if isinstance(data, dict):
                return dict(data)

        return None

"""

def main():
    text = PATH.read_text(encoding="utf-8")

    if "run=self._serialize_record(run)" in text:
        print("Already patched to V2.1.")
        return

    if OLD not in text:
        raise SystemExit("Run serialization anchor not found; refusing unsafe patch.")

    if HELPER_ANCHOR not in text:
        raise SystemExit("Helper anchor not found; refusing unsafe patch.")

    if not BACKUP.exists():
        BACKUP.write_text(text, encoding="utf-8")
        print("Backup:", BACKUP)

    text = text.replace(OLD, NEW, 1)
    text = text.replace(HELPER_ANCHOR, HELPER + HELPER_ANCHOR, 1)

    compile(text, str(PATH), "exec")
    PATH.write_text(text, encoding="utf-8")

    print("Patched:", PATH)
    print("Benchmark Decision Dashboard V2.1 serialization fix: INSTALLED")

if __name__ == "__main__":
    main()
