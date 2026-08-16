from playwright.sync_api import sync_playwright
from comparison.full_comparison_orchestrator import FullComparisonOrchestrator
from comparison.provider_acquisition_router import ProviderAcquisitionRouter
from comparison.evidence_acquisition_orchestrator import EvidenceAcquisitionOrchestrator
from scrapers.arval.evidence_aware_builder import ArvalEvidenceAwareBuilder
from scrapers.ayvens.evidence_aware_builder import AyvensEvidenceAwareBuilder
from scrapers.arval.acquisition_connector import ArvalAcquisitionConnector
from scrapers.ayvens.acquisition_connector import AyvensAcquisitionConnector

ARVAL_URL = "https://www.arval.hu/kis-es-kozepvallalkozasok/tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/byd-atto-2-15-phev-boost-at"
AYVENS_URL = "https://autotartosberlet.ayvens.com/byd/atto-2-dm-i"

def dismiss(page):
    for s in ("#onetrust-reject-all-handler","#onetrust-accept-btn-handler"):
        loc = page.locator(s)
        if loc.count():
            try:
                loc.first.click(timeout=1500)
                return
            except Exception:
                pass

def load(browser, url, builder):
    page = browser.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1800)
        dismiss(page)
        return builder.build(page)
    finally:
        page.close()

def key(wrapped):
    return EvidenceAcquisitionOrchestrator()._vehicle_key(wrapped)

def main():
    print("="*88)
    print("LIVE TARGET CONTRACT DISCOVERY V1")
    print("="*88)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        arval = load(browser, ARVAL_URL, ArvalEvidenceAwareBuilder())
        ayvens = load(browser, AYVENS_URL, AyvensEvidenceAwareBuilder())

        initial = FullComparisonOrchestrator().compare(
            arval, ayvens,
            observed_offer_pool=[arval.composite.offer, ayvens.composite.offer],
        )

        router = ProviderAcquisitionRouter(
            arval_connector=ArvalAcquisitionConnector(browser, canonical_key_builder=key),
            ayvens_connector=AyvensAcquisitionConnector(browser, canonical_key_builder=key),
        )

        plan = router.planner.plan(initial, arval, ayvens)
        routed = [
            router._route_task(t, arval, ayvens)
            for t in plan.by_priority()
            if t.target_dimension == "CONTRACT"
        ]

        print("\n--- ROUTED CONTRACT TARGETS ---")
        for t in routed:
            print(t.provider, "| current=", f"{t.current_duration}/{t.current_mileage}",
                  "| target=", f"{t.target_duration}/{t.target_mileage}")

        execution = router.execute(initial, arval, ayvens)

        print("\n--- CONTRACT ACQUISITION RESULTS ---")
        for c in execution.execution.candidates:
            if c.target_dimension != "CONTRACT":
                continue
            print(c.provider, "|", c.status, "|", c.payload, "|", c.diagnostic)
            if c.accepted:
                rt = next(t for t in routed if t.provider == c.provider)
                assert c.payload.get("duration") == rt.target_duration
                assert c.payload.get("mileage") == rt.target_mileage

        print("\nTEST PASSED - ONLY EXACT TARGET CONTRACT ENDPOINTS CAN BE VALIDATED.")
        browser.close()

if __name__ == "__main__":
    main()
