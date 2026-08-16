from contract_normalization.arval_secondary_financial_evidence_resolver import (
    ArvalSecondaryFinancialEvidenceResolver,
)


def main():
    r = ArvalSecondaryFinancialEvidenceResolver

    generic = r._classify_scope(
        offer_url=(
            "https://www.arval.hu/kis-es-kozepvallalkozasok/"
            "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
            "byd-atto-2-15-phev-boost-at"
        ),
        source_url="https://www.arval.hu/altalanos-feltetelek",
        label="Általános feltételek",
        text=(
            "Induló nettó bérleti díj, önerő, előleg "
            "legfeljebb a jármű értékének 20%-a."
        ),
    )

    assert generic == "GENERIC_PROVIDER_DOCUMENTATION"

    linked = r._classify_scope(
        offer_url=(
            "https://www.arval.hu/kis-es-kozepvallalkozasok/"
            "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
            "byd-atto-2-15-phev-boost-at"
        ),
        source_url="https://www.arval.hu/example",
        label="BYD ATTO 2 PHEV BOOST ajánlat",
        text="BYD ATTO 2 PHEV BOOST pénzügyi feltételek",
    )

    assert linked == "OFFER_LINKED_DOCUMENT"

    parsed = r._parse_explicit_down_payment(
        "Induló nettó bérleti díj: 20%."
    )

    assert parsed is not None
    assert parsed[0] == 20.0

    print(
        "TEST PASSED - SECONDARY FINANCIAL EVIDENCE IS "
        "SCOPE-CLASSIFIED BEFORE PROMOTION."
    )


if __name__ == "__main__":
    main()
