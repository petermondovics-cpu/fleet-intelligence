from types import SimpleNamespace

from scrapers.ayvens.equipment_publication_resolver import (
    PROVIDER_EQUIPMENT_NOT_PUBLISHED,
    PROVIDER_EQUIPMENT_PUBLISHED,
    AyvensEquipmentPublicationResolver,
)


class FakeResponse:
    def __init__(
        self,
        payload,
        status=200,
    ):
        self._payload = payload
        self.status = status
        self.ok = (
            200 <= status < 300
        )

    def json(self):
        return self._payload


class FakeRequest:
    def __init__(self, payload):
        self.payload = payload

    def get(self, url, timeout):
        return FakeResponse(
            self.payload
        )


class FakePage:
    def __init__(self, payload):
        self.request = FakeRequest(
            payload
        )
        self.url = (
            "https://autotartosberlet.ayvens.com/"
            "byd/atto-2-dm-i"
        )


def offer():
    return SimpleNamespace(
        url=(
            "https://autotartosberlet.ayvens.com/"
            "byd/atto-2-dm-i"
        ),
        brand="BYD",
        model="ATTO 2 DM-i",
        trim="Active 166 HP",
        fuel_type="PHEV",
    )


def base_data():
    return {
        "brand": {
            "name": "BYD",
        },
        "model": {
            "name": "ATTO 2 DM-i",
        },
        "configuration": (
            "Active 166 HP"
        ),
        "fuel_type": (
            "Plug-in hibrid"
        ),
    }


def main():
    resolver = (
        AyvensEquipmentPublicationResolver()
    )

    data = base_data()
    data["basic_config"] = []
    data["extra_config"] = []

    result = resolver.resolve(
        FakePage({"data": data}),
        offer(),
    )

    assert (
        result.status
        == PROVIDER_EQUIPMENT_NOT_PUBLISHED
    )

    print(
        "TEST 1 PASSED - EXACT-OFFER API EMPTY LISTS "
        "MEAN PROVIDER LIST NOT_PUBLISHED, NOT ZERO EQUIPMENT."
    )

    data = base_data()
    data["basic_config"] = [
        "Camera",
    ]
    data["extra_config"] = []

    result = resolver.resolve(
        FakePage({"data": data}),
        offer(),
    )

    assert (
        result.status
        == PROVIDER_EQUIPMENT_PUBLISHED
    )

    print(
        "TEST 2 PASSED - NON-EMPTY PROVIDER API LIST "
        "PREVENTS MANUFACTURER FALLBACK."
    )

    data = base_data()
    data["basic_config"] = []
    data["extra_config"] = []
    data["configuration"] = "Boost"

    result = resolver.resolve(
        FakePage({"data": data}),
        offer(),
    )

    assert result.status == "UNRESOLVED"

    print(
        "TEST 3 PASSED - IDENTITY MISMATCH NEVER "
        "CREATES NOT_PUBLISHED EVIDENCE."
    )


if __name__ == "__main__":
    main()
