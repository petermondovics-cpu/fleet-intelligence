from pathlib import Path

PATH = Path("market_intelligence/market_pair_full_comparison_bridge.py")
BACKUP = Path("market_intelligence/market_pair_full_comparison_bridge.py.pre_presenter_v2.bak")

OLD_IMPORT = "from api.comparison_presenter import ComparisonPresenterV1\n"
NEW_IMPORT = "from api.comparison_presenter_v2 import ComparisonPresenterV2\n"

OLD_RESPONSE = """                response = (
                    ComparisonPresenterV1()
                    .present(
                        final,
                        left,
                        right,
"""

NEW_RESPONSE = """                response = (
                    ComparisonPresenterV2()
                    .present(
                        final,
                        decision,
                        left,
                        right,
"""

def main():
    text = PATH.read_text(encoding="utf-8")

    if "ComparisonPresenterV2" in text:
        print("Already patched to ComparisonPresenterV2.")
        return

    if OLD_IMPORT not in text:
        raise SystemExit("ComparisonPresenterV1 import not found; refusing unsafe patch.")
    if OLD_RESPONSE not in text:
        raise SystemExit("ComparisonPresenterV1 final presentation call not found; refusing unsafe patch.")
    if "decision = (" not in text:
        raise SystemExit("Decision layer is not installed. Apply Comparison Decision Explanation V1 first.")

    if not BACKUP.exists():
        BACKUP.write_text(text, encoding="utf-8")
        print("Backup:", BACKUP)

    text = text.replace(OLD_IMPORT, NEW_IMPORT, 1)
    text = text.replace(OLD_RESPONSE, NEW_RESPONSE, 1)

    compile(text, str(PATH), "exec")
    PATH.write_text(text, encoding="utf-8")
    print("Patched:", PATH)
    print("Comparison Presenter V2: INSTALLED")

if __name__ == "__main__":
    main()
