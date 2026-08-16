from typing import List, Optional

from playwright.sync_api import Page, sync_playwright

from core.scraper_plugin import ScraperPlugin
from models.offer import Offer
from models.contract_discovery import (
    ContractDiscoveryEngine,
    DiscoveredContract,
)
from live_contract_collector import LiveContractCollector
from scrapers.arval.cookies import accept_cookies
from scrapers.arval.parser import ArvalParser
from scrapers.arval.offer_route_resolver import (
    ROUTE_LIVE,
    ArvalOfferRouteResolver,
)


ARVAL_URL = (
    "https://www.arval.hu/"
    "kis-es-kozepvallalkozasok/"
    "ajanlat-hosszu-tavu-igenyekre"
)


class ArvalScraper(ScraperPlugin):
    """
    Arval scraper + evidence-based route resolution V2.

    Provider list hrefs are preserved exactly.
    Repeated path segments are NOT rewritten by shape.
    """

    name = "arval"

    def __init__(self):
        self.route_resolver = (
            ArvalOfferRouteResolver()
        )

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

                    continue

            browser.close()

            print(
                f"\nArval collected "
                f"{len(offers)} validated offers"
            )

            return offers

    def collect_offer_urls(
        self,
        page: Page,
    ) -> List[str]:

        page.goto(
            ARVAL_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        accept_cookies(
            page
        )

        page.wait_for_timeout(
            2000
        )

        cards = page.locator(
            "a.is-result-list"
        )

        urls: List[str] = []

        for i in range(
            cards.count()
        ):

            href = (
                cards.nth(i)
                .get_attribute(
                    "href"
                )
            )

            if not href:
                continue

            # Provider-published route is kept verbatim.
            full_url = (
                href
                if href.startswith(
                    "http"
                )
                else "https://www.arval.hu"
                + href
            )

            if full_url not in urls:
                urls.append(
                    full_url
                )

        print(
            f"Found {len(urls)} "
            f"Arval offers"
        )

        return urls

    def collect_offer(
        self,
        page: Page,
        url: str,
    ) -> List[Offer]:

        print(
            f"\nResolving Arval route: {url}"
        )

        route = (
            self.route_resolver
            .resolve(
                page,
                url,
            )
        )

        if (
            route.status
            != ROUTE_LIVE
            or not route.resolved_url
        ):
            raise ValueError(
                "Arval exact-offer route unresolved. "
                + route.diagnostic
            )

        resolved_url = (
            route.resolved_url
        )

        print(
            f"Opening Arval: {resolved_url}"
        )

        try:
            accept_cookies(
                page
            )
        except Exception:
            pass

        parser = ArvalParser()
        discovery = (
            ContractDiscoveryEngine()
        )
        collector = (
            LiveContractCollector()
        )

        title = parser.parse_title(
            page
        )

        fuel_type = (
            parser.parse_fuel_type(
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
            provider="Arval",
            url=resolved_url,
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
                    fuel_type,
                    resolved_url,
                )
            ),
        )

        for item in result.results:

            if (
                item.status
                == "COLLECTED"
            ):

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

    def discover_contracts(
        self,
        page: Page,
        discovery: ContractDiscoveryEngine,
    ) -> List[DiscoveredContract]:

        durations = set()
        mileages = set()

        duration_block = (
            page.locator(
                "p.OfferConfigurationTitle"
            )
            .filter(
                has_text="Időtartam"
            )
            .first
        )

        mileage_block = (
            page.locator(
                "p.OfferConfigurationTitle"
            )
            .filter(
                has_text="Futásteljesítmény"
            )
            .first
        )

        if duration_block.count():

            parent = (
                duration_block.locator(
                    "xpath=.."
                )
            )

            texts = (
                self._visible_texts(
                    parent
                )
            )

            for text in texts:
                value = (
                    discovery
                    ._extract_duration(
                        text
                    )
                )

                if value is not None:
                    durations.add(
                        value
                    )

        if mileage_block.count():

            parent = (
                mileage_block.locator(
                    "xpath=.."
                )
            )

            texts = (
                self._visible_texts(
                    parent
                )
            )

            for text in texts:
                value = (
                    discovery
                    ._extract_mileage(
                        text
                    )
                )

                if value is not None:
                    mileages.add(
                        value
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

    def select_contract(
        self,
        page: Page,
        contract: DiscoveredContract,
    ) -> None:

        self._select_arval_value(
            page,
            "Időtartam",
            [
                f"{contract.duration} hónap",
                f"{contract.duration} hó",
                str(
                    contract.duration
                ),
            ],
        )

        page.wait_for_timeout(
            500
        )

        self._select_arval_value(
            page,
            "Futásteljesítmény",
            [
                f"{contract.mileage:,} km/év".replace(
                    ",",
                    " ",
                ),
                f"{contract.mileage:,} km/év",
                f"{contract.mileage} km/év",
                str(
                    contract.mileage
                ),
            ],
        )

        page.wait_for_timeout(
            700
        )

    def parse_selected_contract(
        self,
        page: Page,
        parser: ArvalParser,
        title: str,
        fuel_type: str,
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

        return Offer(
            provider="Arval",
            brand="",
            model=title,
            trim="",
            fuel_type=fuel_type,
            monthly_fee=monthly_fee,
            duration=duration,
            mileage=mileage,
            url=url,
        )

    def _select_arval_value(
        self,
        page: Page,
        label: str,
        candidates: List[str],
    ) -> None:

        block = (
            page.locator(
                "p.OfferConfigurationTitle"
            )
            .filter(
                has_text=label
            )
            .first
        )

        if block.count() == 0:
            raise ValueError(
                f"Arval label not found: {label}"
            )

        parent = block.locator(
            "xpath=.."
        )

        select = parent.locator(
            "select"
        )

        for i in range(
            select.count()
        ):

            current = select.nth(i)

            options = current.locator(
                "option"
            )

            for j in range(
                options.count()
            ):

                option = options.nth(
                    j
                )

                text = (
                    option.inner_text()
                    .strip()
                )

                value = (
                    option.get_attribute(
                        "value"
                    )
                )

                if self._matches(
                    text,
                    value,
                    candidates,
                ):

                    if value is not None:
                        current.select_option(
                            value=value
                        )
                    else:
                        current.select_option(
                            label=text
                        )

                    return

        controls = parent.locator(
            "button, label, "
            "[role='option'], "
            "[role='radio'], "
            "[role='button']"
        )

        for i in range(
            controls.count()
        ):

            control = controls.nth(
                i
            )

            try:
                text = (
                    control.inner_text()
                    .strip()
                )
            except Exception:
                continue

            if self._matches(
                text,
                None,
                candidates,
            ):

                control.click(
                    timeout=5000
                )

                return

        raise ValueError(
            f"Arval value not found "
            f"for {label}: {candidates}"
        )

    @staticmethod
    def _matches(
        text: str,
        value: Optional[str],
        candidates: List[str],
    ) -> bool:

        haystacks = [
            text or "",
            value or "",
        ]

        for haystack in haystacks:

            normalized = (
                haystack
                .strip()
                .lower()
                .replace(".", "")
                .replace(",", "")
                .replace(" ", "")
                .replace("/", "")
            )

            for candidate in candidates:

                expected = (
                    candidate
                    .strip()
                    .lower()
                    .replace(".", "")
                    .replace(",", "")
                    .replace(" ", "")
                    .replace("/", "")
                )

                if (
                    expected
                    and expected
                    == normalized
                ):
                    return True

        return False

    @staticmethod
    def _visible_texts(
        locator,
    ) -> List[str]:

        result = []

        try:

            for i in range(
                locator.count()
            ):

                item = locator.nth(
                    i
                )

                if not item.is_visible():
                    continue

                text = (
                    item.inner_text()
                    .strip()
                )

                if text:
                    result.append(
                        text
                    )

        except Exception:
            pass

        return result

    @staticmethod
    def _format_contracts(
        contracts: List[
            DiscoveredContract
        ],
    ) -> str:

        if not contracts:
            return "NONE"

        return ", ".join(
            f"{item.duration}/{item.mileage}"
            for item in contracts
        )
