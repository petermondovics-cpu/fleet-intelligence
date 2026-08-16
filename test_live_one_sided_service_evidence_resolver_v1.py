from playwright.sync_api import sync_playwright
from comparison.one_sided_service_evidence_resolver import OneSidedServiceEvidenceResolver
from scrapers.arval.acquisition_connector import ArvalAcquisitionConnector
from scrapers.ayvens.acquisition_connector import AyvensAcquisitionConnector

ARVAL_ATTO = "https://www.arval.hu/kis-es-kozepvallalkozasok/tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/byd-atto-2-15-phev-boost-at"
AYVENS_ATTO = "https://autotartosberlet.ayvens.com/byd/atto-2-dm-i"

class Task:
    provider = None
    current_url = None

def key(_): return "TEST"

def collect(connector, provider, url):
    t = Task(); t.provider = provider; t.current_url = url
    raw = connector.service_discovery(t)
    return () if raw is None else (raw,)

def main():
    print("="*88)
    print("LIVE ONE-SIDED SERVICE EVIDENCE RESOLVER V1")
    print("="*88)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        arval = ArvalAcquisitionConnector(browser, canonical_key_builder=key)
        ayvens = AyvensAcquisitionConnector(browser, canonical_key_builder=key)

        results = OneSidedServiceEvidenceResolver().resolve_gaps(
            arval_sources=collect(arval,"Arval",ARVAL_ATTO),
            ayvens_sources=collect(ayvens,"Ayvens",AYVENS_ATTO),
        )

        for item in results:
            print(item.provider, "|", item.canonical_code, "|", item.status, "| included=", item.included, "| scope=", item.applicability_scope)
            print(" diagnostic:", item.diagnostic)

        assert len(results) == 3
        print("\nTEST PASSED - LIVE TARGETED RESOLVER EVALUATED THE THREE OPEN SERVICE GAPS SAFELY.")
        browser.close()

if __name__ == "__main__":
    main()
