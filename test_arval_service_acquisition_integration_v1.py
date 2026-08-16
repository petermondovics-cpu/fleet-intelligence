from types import SimpleNamespace

from scrapers.arval.acquisition_connector_integrated import (
    ArvalServiceIntegratedAcquisitionConnector,
)


class BaseFake:
    pass


def main():
    # Test the payload contract independently from live Playwright by
    # constructing an instance without invoking the parent initializer.
    connector = object.__new__(
        ArvalServiceIntegratedAcquisitionConnector
    )

    connector.exact_offer_service_resolver = (
        SimpleNamespace(
            resolve=lambda url: SimpleNamespace(
                status="VALIDATED",
                evidence=(
                    SimpleNamespace(
                        code="INSURANCE",
                        source_text="Biztosítás",
                        applicability_scope="EXACT_OFFER",
                    ),
                    SimpleNamespace(
                        code="MAINTENANCE",
                        source_text="Karbantartás",
                        applicability_scope="EXACT_OFFER",
                    ),
                ),
            )
        )
    )

    # Avoid fallback in this unit test by giving valid exact evidence.
    task = SimpleNamespace(
        current_url="https://example.test/arval"
    )

    result = (
        ArvalServiceIntegratedAcquisitionConnector
        .service_discovery(
            connector,
            task,
        )
    )

    assert result is not None
    assert (
        result["applicability_scope"]
        == "EXACT_OFFER"
    )
    assert (
        result["source_type"]
        == "PROVIDER_OFFER_PAGE_DOM"
    )
    assert (
        result["evidence_method"]
        == "STRUCTURED_SERVICE_ACCORDION_DOM"
    )

    codes = {
        item["code"]
        for item in result["services"]
    }

    assert codes == {
        "INSURANCE",
        "MAINTENANCE",
    }

    assert all(
        item["included"] is True
        for item in result["services"]
    )

    print(
        "TEST PASSED - ARVAL INTEGRATED CONNECTOR "
        "PROMOTES STRUCTURED EXACT-OFFER SERVICES "
        "IN THE ACQUISITION EXECUTOR PAYLOAD SHAPE."
    )


if __name__ == "__main__":
    main()
