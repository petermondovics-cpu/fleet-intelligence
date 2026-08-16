from comparison.arval_exact_offer_service_evidence_resolver import (
    ArvalExactOfferServiceEvidenceResolver,
)


def main():

    r = (
        ArvalExactOfferServiceEvidenceResolver
    )

    text = """
    BYD ATTO 2
    192312 FT +ÁFA / hónap
    Időtartam 60 hónap
    Futásteljesítmény 20000 km/év

    6 szolgáltatás az Arvaltól a csomagban

    Biztosítás és káresemény-kezelés
    A biztosítások és a káresemény kezelés minden területével foglalkozunk.

    Finanszírozás
    A flottakezelés minden vonatkozása egyetlen rögzített havi díjért.

    Szerviz és karbantartás
    A gépjármű karbantartását kezeljük.

    Gumicsere
    Szezonális gumicsere.

    Közúti segítségnyújtás
    Segítség útközben.

    Miért válassza az Arvalt?
    Adózási tanácsadás általános vállalati szolgáltatásként.
    """

    region = r._extract_package_region(
        text
    )

    assert region is not None

    services = r._extract_services(
        text=region,
        source_url="https://example.test/offer",
        scope="EXACT_OFFER",
        source_type="PROVIDER_OFFER_PAGE",
    )

    codes = {
        item.code
        for item in services
    }

    assert "INSURANCE" in codes
    assert "CLAIMS_MANAGEMENT" in codes
    assert "FINANCING" in codes
    assert "MAINTENANCE" in codes
    assert "TYRES" in codes
    assert "ROADSIDE_ASSISTANCE" in codes

    # Text after the package-region stop marker must not leak into
    # exact-offer evidence.
    assert "TAXES" not in codes

    print(
        "TEST PASSED - ARVAL EXACT-OFFER SERVICE RESOLVER "
        "PROMOTES ONLY SERVICES INSIDE THE OFFER PACKAGE REGION."
    )


if __name__ == "__main__":
    main()
