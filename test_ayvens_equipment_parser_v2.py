from scrapers.ayvens.equipment_parser import (
    AyvensEquipmentParser,
    EQUIPMENT_NOT_PUBLISHED,
    EQUIPMENT_PARSING_UNRESOLVED,
    EQUIPMENT_PUBLISHED,
)


class FakeLocator:

    def __init__(
        self,
        text="",
        attrs=None,
        count_value=1,
        visible=True,
        children=None,
    ):
        self._text = text
        self._attrs = attrs or {}
        self._count = count_value
        self._visible = visible
        self._children = children or {}
        self.clicked = False

    @property
    def first(self):
        return self

    def count(self):
        return self._count

    def nth(self, index):
        return self._children.get(
            ("nth", index),
            FakeLocator(count_value=0),
        )

    def inner_text(self):
        return self._text

    def is_visible(self):
        return self._visible

    def get_attribute(self, name):
        return self._attrs.get(name)

    def click(self, timeout=5000):
        self.clicked = True
        self._attrs["aria-selected"] = "true"

    def scroll_into_view_if_needed(self):
        pass

    def locator(self, selector):
        return self._children.get(
            selector,
            FakeLocator(count_value=0),
        )


class FakePage:

    def __init__(
        self,
        tabs=None,
        panels=None,
    ):
        self.url = "https://example.com/ayvens"
        self.tabs = tabs or {}
        self.panels = panels or {}

    def get_by_role(
        self,
        role,
        name=None,
        exact=True,
    ):
        if role == "tab":
            return self.tabs.get(
                name,
                FakeLocator(count_value=0),
            )

        return FakeLocator(count_value=0)

    def get_by_text(
        self,
        text,
        exact=True,
    ):
        return self.tabs.get(
            text,
            FakeLocator(count_value=0),
        )

    def locator(self, selector):
        if selector.startswith("#"):
            return self.panels.get(
                selector[1:],
                FakeLocator(count_value=0),
            )

        if selector == "[role='tabpanel']":
            visible = [
                p
                for p in self.panels.values()
                if p.is_visible()
            ]

            children = {
                ("nth", i): value
                for i, value in enumerate(visible)
            }

            return FakeLocator(
                count_value=len(visible),
                children=children,
            )

        return FakeLocator(count_value=0)

    def wait_for_timeout(self, ms):
        pass


def make_nodes(texts):
    children = {}

    for index, text in enumerate(texts):
        children[
            ("nth", index)
        ] = FakeLocator(
            text=text,
            children={
                ":scope > *": FakeLocator(
                    count_value=0
                )
            },
        )

    return FakeLocator(
        count_value=len(texts),
        children=children,
    )


def make_panel(texts):
    return FakeLocator(
        text="\n".join(texts),
        attrs={"role": "tabpanel"},
        children={
            "li": make_nodes(texts),
            "[role='listitem']": FakeLocator(
                count_value=0
            ),
            "p": FakeLocator(count_value=0),
            "span": FakeLocator(count_value=0),
            "div": FakeLocator(count_value=0),
        },
    )


def make_tab(label, panel_id):
    return FakeLocator(
        text=label,
        attrs={
            "aria-selected": "true",
            "aria-controls": panel_id,
        },
    )


def main():

    parser = AyvensEquipmentParser()

    # TEST 1: missing tab = genuinely not published
    page = FakePage()

    result = parser.parse_standard_equipment(
        page
    )

    assert (
        result.status
        == EQUIPMENT_NOT_PUBLISHED
    )

    print(
        "TEST 1 PASSED - "
        "MISSING TAB IS NOT_PUBLISHED"
    )

    # TEST 2: tab exists but empty parser result = unresolved
    tab = make_tab(
        "Alapfelszereltség",
        "standard-panel",
    )

    page = FakePage(
        tabs={
            "Alapfelszereltség": tab,
        },
        panels={
            "standard-panel": make_panel([]),
        },
    )

    result = parser.parse_standard_equipment(
        page
    )

    assert (
        result.status
        == EQUIPMENT_PARSING_UNRESOLVED
    )

    print(
        "TEST 2 PASSED - "
        "EMPTY EXISTING TAB IS PARSING_UNRESOLVED"
    )

    # TEST 3: standard equipment
    standard_texts = [
        "Tető a karosszéria színében",
        "Elektromosan állítható, fűthető külső tükrök",
        "Vonóhorog-előkészítés",
    ]

    page = FakePage(
        tabs={
            "Alapfelszereltség": tab,
        },
        panels={
            "standard-panel": make_panel(
                standard_texts
            ),
        },
    )

    result = parser.parse_standard_equipment(
        page
    )

    assert (
        result.status
        == EQUIPMENT_PUBLISHED
    )

    assert result.item_count == 3

    assert all(
        item.standard is True
        for item in result.items
    )

    assert all(
        item.included is True
        for item in result.items
    )

    print(
        "TEST 3 PASSED - "
        "STANDARD EQUIPMENT PARSED"
    )

    # TEST 4: observed evidence
    assert all(
        item.evidence.status == "OBSERVED"
        for item in result.items
    )

    print(
        "TEST 4 PASSED - "
        "STANDARD EQUIPMENT EVIDENCE ATTACHED"
    )

    # TEST 5: built-in extras are separate
    optional_tab = make_tab(
        "Beépített extra felszereltség",
        "optional-panel",
    )

    optional_texts = [
        "Metálfényezés",
        "Tolatókamera",
    ]

    page = FakePage(
        tabs={
            "Beépített extra felszereltség": (
                optional_tab
            ),
        },
        panels={
            "optional-panel": make_panel(
                optional_texts
            ),
        },
    )

    result = parser.parse_optional_equipment(
        page
    )

    assert (
        result.status
        == EQUIPMENT_PUBLISHED
    )

    assert result.item_count == 2

    assert all(
        item.standard is False
        for item in result.items
    )

    print(
        "TEST 5 PASSED - "
        "BUILT-IN EXTRA EQUIPMENT PARSED SEPARATELY"
    )

    # TEST 6: no silent equipment inference
    page = FakePage(
        tabs={
            "Beépített extra felszereltség": (
                optional_tab
            ),
        },
        panels={
            "optional-panel": make_panel([]),
        },
    )

    result = parser.parse_optional_equipment(
        page
    )

    assert (
        result.status
        == EQUIPMENT_PARSING_UNRESOLVED
    )

    assert result.items == []

    print(
        "TEST 6 PASSED - "
        "NO SILENT EQUIPMENT INFERENCE"
    )

    print(
        "\nALL AYVENS EQUIPMENT "
        "PARSER V2 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
