from pathlib import Path

PATH = Path("market_intelligence/market_pair_full_comparison_bridge.py")
BACKUP = Path("market_intelligence/market_pair_full_comparison_bridge.py.pre_contract_v3.bak")

OLD_IMPORT = """from contract_normalization.contract_normalization_evidence_resolver_v2 import (
    ContractNormalizationEvidenceResolverV2,
)
"""
NEW_IMPORT = """from contract_normalization.contract_normalization_evidence_resolver_v3 import (
    ContractNormalizationEvidenceResolverV3,
)
"""

OLD_CALL = """                contract_evidence = (
                    ContractNormalizationEvidenceResolverV2(
                        browser
                    )
                    .resolve(
                        left.composite.offer,
                        right.composite.offer,
                    )
                )
"""
NEW_CALL = """                contract_evidence = (
                    ContractNormalizationEvidenceResolverV3(
                        browser
                    )
                    .resolve(
                        left.composite.offer,
                        right.composite.offer,
                    )
                )
"""

def main():
    text = PATH.read_text(encoding="utf-8")
    if "ContractNormalizationEvidenceResolverV3" in text:
        print("Already patched to V3.")
        return
    if OLD_IMPORT not in text or OLD_CALL not in text:
        raise SystemExit("V2 anchors not found; refusing unsafe patch.")
    if not BACKUP.exists():
        BACKUP.write_text(text, encoding="utf-8")
        print("Backup:", BACKUP)
    text = text.replace(OLD_IMPORT, NEW_IMPORT, 1)
    text = text.replace(OLD_CALL, NEW_CALL, 1)
    compile(text, str(PATH), "exec")
    PATH.write_text(text, encoding="utf-8")
    print("Patched:", PATH)
    print("Contract V3 bridge integration: INSTALLED")

if __name__ == "__main__":
    main()
