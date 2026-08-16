from typing import List

from playwright.sync_api import Page, sync_playwright

from core.scraper_plugin import ScraperPlugin
from models.offer import Offer
from models.contract_discovery import (
    ContractDiscoveryEngine,
    DiscoveredContract,
)
from live_contract_collector import LiveContractCollector
from scrapers.ayvens.parser import AyvensParser


AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/"
)


class AyvensScraper(ScraperPlugin):

    name = "ayvens"

    # ============================================================
    # COLLECTION
    # ============================================================

    def collect(self) -> List[Offer]:

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=False
            )

            page = browser.new_page()

            urls = self.collect_offer_urls(
                page
            )

            offers: List[Offer] = []

            for url in urls:

                try:

                    collected = (
                        self.collect_offer(
                            page,
                            url,
                        )
                    )

                    offers.extend(
                        collected
                    )

                except Exception as exc:

                    print(
                        f"❌ Failed: {url}"
                    )
                    print(exc)

            browser.close()

            print(
                f"\nAyvens collected "
                f"{len(offers)} validated offers"
            )

            return offers

    # ============================================================
    # URL DISCOVERY
    # ============================================================

    def collect_offer_urls(
        self,
        page: Page,
    ) -> List[str]:

        page.goto(
            AYVENS_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(
            5000
        )

        cards = page.locator(
            "div.card-container"
        )

        print(
            f"Detected card containers: "
            f"{cards.count()}"
        )

        urls: List[str] = []

        for i in range(
            cards.count()
        ):

            card = cards.nth(i)

            link = card.locator(
                "xpath=ancestor::a[1]"
            )

            if link.count() == 0:
                continue

            href = link.get_attribute(
                "href"
            )

            if not href:
                continue

            if href.startswith(
                "http"
            ):
                full_url = href

            else:
                full_url = (
                    "https://autotartosberlet.ayvens.com"
                    + href
                )

            if full_url not in urls:
                urls.append(
                    full_url
                )

        print(
            f"Found {len(urls)} "
            f"Ayvens offers"
        )

        return urls

    # ============================================================
    # ONE OFFER / ONE URL
    # ============================================================

    def collect_offer(
        self,
        page: Page,
        url: str,
    ) -> List[Offer]:

        print(
            f"\nOpening Ayvens: {url}"
        )

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(
            2000
        )

        self.dismiss_cookies(
            page
        )

        parser = AyvensParser()

        discovery = (
            ContractDiscoveryEngine()
        )

        collector = (
            LiveContractCollector()
        )

        title = (
            parser.parse_title(
                page
            )
        )

        model = (
            parser.parse_model(
                page
            )
        )

        contracts = (
            self.discover_contracts(
                page,
                discovery,
            )
        )

        print(
            "Discovered contracts: "
            + self._format_contracts(
                contracts
            )
        )

        result = collector.collect(
            provider="Ayvens",
            url=url,
            contracts=contracts,

            select_contract=lambda contract: (
                self.select_contract(
                    page,
                    contract,
                )
            ),

            parse_selected_contract=lambda contract: (
                self.parse_selected_contract(
                    page,
                    parser,
                    title,
                    model,
                    url,
                )
            ),
        )

        for item in result.results:

            if item.status == "COLLECTED":

                print(
                    "🟢 Collected: "
                    f"{item.contract.duration} hó / "
                    f"{item.contract.mileage:,} km"
                )

                print(
                    f"   {item.offer.monthly_fee:,} Ft"
                )

            else:

                print(
                    "⚠️ Rejected: "
                    f"{item.contract.duration} hó / "
                    f"{item.contract.mileage:,} km"
                )

                print(
                    f"   {item.reason}"
                )

        return result.offers

    # ============================================================
    # CONTRACT DISCOVERY
    # ============================================================

    def discover_contracts(
        self,
        page: Page,
        discovery: ContractDiscoveryEngine,
    ) -> List[DiscoveredContract]:

        durations = set()
        mileages = set()

        summaries = page.locator(
            "p.font-size-16px.font-source"
        )

        for i in range(
            summaries.count()
        ):

            item = summaries.nth(i)

            try:

                if not item.is_visible():
                    continue

                text = (
                    item
                    .inner_text()
                    .strip()
                )

            except Exception:
                continue

            duration = (
                discovery._extract_duration(
                    text
                )
            )

            mileage = (
                discovery._extract_mileage(
                    text
                )
            )

            if duration is not None:
                durations.add(
                    duration
                )

            if mileage is not None:
                mileages.add(
                    mileage
                )

        return [
            DiscoveredContract(
                duration=duration,
                mileage=mileage,
            )
            for duration in sorted(
                durations
            )
            for mileage in sorted(
                mileages
            )
        ]

    # ============================================================
    # CONTRACT SELECTION
    # ============================================================

    def select_contract(
        self,
        page: Page,
        contract: DiscoveredContract,
    ) -> None:

        print(
            f"Ayvens selecting: "
            f"{contract.duration} hó / "
            f"{contract.mileage:,} km"
        )

        self._select_duration(
            page,
            contract.duration,
        )

        page.wait_for_timeout(
            700
        )

        self._select_mileage(
            page,
            contract.mileage,
        )

        page.wait_for_timeout(
            1000
        )

    # ============================================================
    # DURATION SELECTOR
    #
    # Ayvens uses:
    #
    # input[type=range]
    # min=36
    # max=60
    # step=12
    # ============================================================

    def _select_duration(
        self,
        page: Page,
        duration: int,
    ) -> None:

        ranges = page.locator(
            "input[type='range']"
        )

        control = None

        for i in range(
            ranges.count()
        ):

            candidate = ranges.nth(i)

            try:

                if not candidate.is_visible():
                    continue

            except Exception:
                continue

            minimum = (
                candidate.get_attribute(
                    "min"
                )
            )

            maximum = (
                candidate.get_attribute(
                    "max"
                )
            )

            step = (
                candidate.get_attribute(
                    "step"
                )
            )

            if (
                minimum == "36"
                and maximum == "60"
                and step == "12"
            ):

                control = candidate
                break

        if control is None:

            raise ValueError(
                f"Ayvens duration control "
                f"not found for "
                f"{duration} months"
            )

        self._set_range_value(
            control,
            duration,
        )

        page.wait_for_timeout(
            800
        )

        observed = int(
            control.input_value()
        )

        if observed != duration:

            raise ValueError(
                "Ayvens duration selection failed: "
                f"requested={duration}, "
                f"observed={observed}"
            )

    # ============================================================
    # MILEAGE SELECTOR
    #
    # Ayvens uses:
    #
    # input[type=range]
    # min=20000
    # max=60000
    # step=10000
    #
    # THIS IS THE IMPORTANT FIX.
    # ============================================================

    def _select_mileage(
        self,
        page: Page,
        mileage: int,
    ) -> None:

        ranges = page.locator(
            "input[type='range']"
        )

        control = None

        for i in range(
            ranges.count()
        ):

            candidate = ranges.nth(i)

            try:

                if not candidate.is_visible():
                    continue

            except Exception:
                continue

            minimum = (
                candidate.get_attribute(
                    "min"
                )
            )

            maximum = (
                candidate.get_attribute(
                    "max"
                )
            )

            step = (
                candidate.get_attribute(
                    "step"
                )
            )

            # This uniquely identifies the
            # Ayvens mileage slider.

            if (
                minimum == "20000"
                and maximum == "60000"
                and step == "10000"
            ):

                control = candidate
                break

        if control is None:

            raise ValueError(
                f"Ayvens mileage control "
                f"not found for "
                f"{mileage} km/year"
            )

        minimum = int(
            control.get_attribute(
                "min"
            )
        )

        maximum = int(
            control.get_attribute(
                "max"
            )
        )

        step = int(
            control.get_attribute(
                "step"
            )
        )

        if (
            mileage < minimum
            or mileage > maximum
        ):

            raise ValueError(
                f"Ayvens mileage "
                f"{mileage} outside range "
                f"{minimum}-{maximum}"
            )

        if (
            (mileage - minimum)
            % step
            != 0
        ):

            raise ValueError(
                f"Ayvens mileage "
                f"{mileage} does not match "
                f"step {step}"
            )

        self._set_range_value(
            control,
            mileage,
        )

        page.wait_for_timeout(
            800
        )

        observed = int(
            control.input_value()
        )

        if observed != mileage:

            raise ValueError(
                "Ayvens mileage selection failed: "
                f"requested={mileage}, "
                f"observed={observed}"
            )

    # ============================================================
    # RANGE INPUT HELPER
    # ============================================================

    @staticmethod
    def _set_range_value(
        control,
        value: int,
    ) -> None:

        current = int(
            control.input_value()
        )

        if current == value:
            return

        control.evaluate(
            """
            (el, target) => {

                const setter =
                    Object.getOwnPropertyDescriptor(
                        HTMLInputElement.prototype,
                        'value'
                    ).set;

                setter.call(
                    el,
                    String(target)
                );

                el.dispatchEvent(
                    new Event(
                        'input',
                        {
                            bubbles: true
                        }
                    )
                );

                el.dispatchEvent(
                    new Event(
                        'change',
                        {
                            bubbles: true
                        }
                    )
                );
            }
            """,
            value,
        )

    # ============================================================
    # PARSE SELECTED CONTRACT
    # ============================================================

    def parse_selected_contract(
        self,
        page: Page,
        parser: AyvensParser,
        title: str,
        model: str,
        url: str,
    ) -> Offer:

        duration = (
            parser.parse_duration(
                page
            )
        )

        mileage = (
            parser.parse_mileage(
                page
            )
        )

        monthly_fee = (
            parser.parse_monthly_fee(
                page
            )
        )

        fuel_type = (
            parser.parse_fuel_type(
                page
            )
        )

        return Offer(
            provider="Ayvens",
            brand="",
            model=title,
            trim=model,
            fuel_type=fuel_type,
            monthly_fee=monthly_fee,
            duration=duration,
            mileage=mileage,
            url=url,
        )

    # ============================================================
    # COOKIES
    # ============================================================

    @staticmethod
    def dismiss_cookies(
        page: Page,
    ) -> None:

        selectors = [
            "#onetrust-reject-all-handler",
            "#onetrust-accept-btn-handler",
            "button:has-text('Összes elfogadása')",
            "button:has-text('Elutasítom')",
            "button:has-text('Elfogadom')",
        ]

        for selector in selectors:

            locator = page.locator(
                selector
            )

            if locator.count() == 0:
                continue

            try:

                locator.first.click(
                    timeout=3000
                )

                page.wait_for_timeout(
                    500
                )

                return

            except Exception:
                continue

    # ============================================================
    # DISPLAY
    # ============================================================

    @staticmethod
    def _format_contracts(
        contracts: List[DiscoveredContract],
    ) -> str:

        if not contracts:
            return "NONE"

        return ", ".join(
            f"{item.duration}/{item.mileage}"
            for item in contracts
        )
