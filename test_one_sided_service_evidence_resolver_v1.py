from comparison.one_sided_service_evidence_resolver import *

def main():
    r = OneSidedServiceEvidenceResolver()

    x = r.resolve_candidate(provider="Arval", canonical_code="TAXES", source_type="PROVIDER_SERVICE_PAGE", source_url="x", source_text="Az adók kezeléséről itt talál információt.", applicability_scope="GENERIC_PROVIDER_DOCUMENTATION")
    assert x.status == SERVICE_UNRESOLVED
    print("TEST 1 PASSED")

    x = r.resolve_candidate(provider="Arval", canonical_code="TAXES", source_type="PROVIDER_TERMS_OR_PDF", source_url="x", source_text="Minden tartós bérleti ajánlatunk tartalmazza a vonatkozó adókat.", applicability_scope="GENERIC_PROVIDER_DOCUMENTATION")
    assert x.status == SERVICE_TRUE
    print("TEST 2 PASSED")

    x = r.resolve_candidate(provider="Ayvens", canonical_code="FINANCING", source_type="PROVIDER_OFFER_PAGE", source_url="x", source_text="A finanszírozás külön díj ellenében vehető igénybe.", applicability_scope="EXACT_OFFER")
    assert x.status == SERVICE_FALSE
    print("TEST 3 PASSED")

    x = r.resolve_candidate(provider="Ayvens", canonical_code="CLAIMS_MANAGEMENT", source_type="PROVIDER_OFFER_PAGE", source_url="x", source_text="Káresemény esetén kérjük, hívja ügyfélszolgálatunkat.", applicability_scope="EXACT_OFFER")
    assert x.status == SERVICE_UNRESOLVED
    print("TEST 4 PASSED")

    x = r.resolve_candidate(provider="Ayvens", canonical_code="FINANCING", source_type="PROVIDER_OFFER_PAGE", source_url="x", source_text="Teljes körű karbantartás és assistance.", applicability_scope="EXACT_OFFER")
    assert x.status == SERVICE_UNRESOLVED and x.included is None
    print("TEST 5 PASSED")

    print("\nALL ONE-SIDED SERVICE EVIDENCE RESOLVER V1 TESTS PASSED")

if __name__ == "__main__":
    main()
