from playwright.sync_api import sync_playwright

from scrapers.arval.acquisition_connector import ArvalAcquisitionConnector
from scrapers.ayvens.acquisition_connector import AyvensAcquisitionConnector

class Task:
    provider = None
    current_url = None

ARVAL_ATTO = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)

AYVENS_ATTO = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)

def key(_):
    return "TEST"

def main():
    print("=" * 80)
    print("LIVE SERVICE APPLICABILITY SCOPE V1")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        arval = ArvalAcquisitionConnector(
            browser,
            canonical_key_builder=key,
        )
        ayvens = AyvensAcquisitionConnector(
            browser,
            canonical_key_builder=key,
        )

        at = Task()
        at.provider = "Arval"
        at.current_url = ARVAL_ATTO

        yt = Task()
        yt.provider = "Ayvens"
        yt.current_url = AYVENS_ATTO

        ar = arval.service_discovery(at)
        yr = ayvens.service_discovery(yt)

        print("\nARVAL")
        if ar is None:
            print("UNRESOLVED")
        else:
            print("source:", ar["source_type"])
            print("scope:", ar.get("applicability_scope"))
            print("assertions:", len(ar.get("services") or ()))

        print("\nAYVENS")
        if yr is None:
            print("UNRESOLVED")
        else:
            print("source:", yr["source_type"])
            print("scope:", yr.get("applicability_scope"))
            print("assertions:", len(yr.get("services") or ()))
            for item in yr.get("services") or ():
                print("-", item)

        if ar is not None:
            assert (
                ar.get("applicability_scope")
                == "GENERIC_PROVIDER_DOCUMENTATION"
            )

        assert yr is not None
        assert yr.get("applicability_scope") == "EXACT_OFFER"
        assert yr["source_type"] == "PROVIDER_OFFER_PAGE"
        assert len(yr.get("services") or ()) > 0

        print(
            "\nTEST PASSED - ARVAL GENERIC DOCS REMAIN GENERIC; "
            "AYVENS CURRENT-OFFER SERVICES ARE EXACT_OFFER."
        )

        browser.close()

if __name__ == "__main__":
    main()
