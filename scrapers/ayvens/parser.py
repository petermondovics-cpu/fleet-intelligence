import re

from playwright.sync_api import Page


class AyvensParser:

    # ============================================================
    # BASIC PARSING
    # ============================================================

    def parse_title(self, page: Page) -> str:
        return (
            page.locator(
                "h2.fw-500.font-size-28px"
            )
            .first
            .inner_text()
            .strip()
        )

    def parse_model(self, page: Page) -> str:
        return (
            page.locator(
                "div.font-size-18px.fw-400.font-source.color-blue"
            )
            .first
            .inner_text()
            .strip()
        )

    def parse_monthly_fee(self, page: Page) -> int:

        locator = (
            page.locator(
                "div.font-size-40px.font-size-40px"
            )
        )

        if locator.count() == 0:
            locator = page.locator(
                "div.font-size-40px.fw-500.whitespace-nowrap"
            )

        if locator.count() == 0:
            raise ValueError(
                "Ayvens monthly fee not found"
            )

        text = (
            locator
            .first
            .inner_text()
            .strip()
        )

        digits = re.sub(
            r"\D",
            "",
            text,
        )

        if not digits:
            raise ValueError(
                f"Invalid monthly fee: '{text}'"
            )

        return int(digits)

    def parse_duration(
        self,
        page: Page,
    ) -> int:

        text = (
            page.locator(
                "p.font-size-16px.font-source.color-\\#757777"
            )
            .first
            .inner_text()
            .strip()
        )

        match = re.search(
            r"(\d+)\s*hónap",
            text,
        )

        if not match:
            raise ValueError(
                f"Duration not found: '{text}'"
            )

        return int(
            match.group(1)
        )

    def parse_mileage(
        self,
        page: Page,
    ) -> int:

        text = (
            page.locator(
                "p.font-size-16px.font-source.color-\\#757777"
            )
            .first
            .inner_text()
            .strip()
        )

        match = re.search(
            r"([\d\.]+)\s*km/év",
            text,
        )

        if not match:
            raise ValueError(
                f"Mileage not found: '{text}'"
            )

        return int(
            match.group(1)
            .replace(".", "")
        )

    def parse_fuel_type(
        self,
        page: Page,
    ) -> str:

        text = (
            page.locator(
                "strong.fw-700"
            )
            .first
            .inner_text()
            .strip()
        )

        mapping = {
            "100% elektromos": "EV",
            "Elektromos": "EV",
            "Plug-in hibrid": "PHEV",
            "Hibrid": "Hybrid",
            "Benzin": "Petrol",
            "Dízel": "Diesel",
        }

        return mapping.get(
            text,
            text,
        )

    # ============================================================
    # CONTRACT CONTROLS
    #
    # Ayvens:
    #
    # Futamidő:
    #   input[type=range]
    #   min=36
    #   max=60
    #   step=12
    #
    # Futásteljesítmény:
    #   input[type=range]
    #   min=20000
    #   max=60000
    #   step=10000
    #
    # A diagnosztika alapján mindkettő a #slider-input
    # konténerben található.
    # ============================================================

    def _find_duration_control(
        self,
        page: Page,
    ):

        control = (
            page.locator("#slider-input")
            .filter(
                has_text="Futamidő"
            )
            .locator(
                "input[type='range']"
            )
            .first
        )

        if control.count() == 0:

            # Fallback: keressük az összes range inputot
            # és az attribútumok alapján azonosítjuk.
            ranges = page.locator(
                "input[type='range']"
            )

            for i in range(
                ranges.count()
            ):

                candidate = ranges.nth(i)

                minimum = candidate.get_attribute(
                    "min"
                )

                maximum = candidate.get_attribute(
                    "max"
                )

                step = candidate.get_attribute(
                    "step"
                )

                if (
                    minimum == "36"
                    and maximum == "60"
                    and step == "12"
                ):
                    return candidate

            raise ValueError(
                "Ayvens duration control not found"
            )

        return control

    def _find_mileage_control(
        self,
        page: Page,
    ):

        control = (
            page.locator("#slider-input")
            .filter(
                has_text="Futásteljesítmény"
            )
            .locator(
                "input[type='range']"
            )
            .first
        )

        if control.count() == 0:

            # Fallback: keressük az összes range inputot
            # és az attribútumok alapján azonosítjuk.
            ranges = page.locator(
                "input[type='range']"
            )

            for i in range(
                ranges.count()
            ):

                candidate = ranges.nth(i)

                minimum = candidate.get_attribute(
                    "min"
                )

                maximum = candidate.get_attribute(
                    "max"
                )

                step = candidate.get_attribute(
                    "step"
                )

                if (
                    minimum == "20000"
                    and maximum == "60000"
                    and step == "10000"
                ):
                    return candidate

            raise ValueError(
                "Ayvens mileage control not found"
            )

        return control

    # ============================================================
    # SELECT DURATION
    # ============================================================

    def _select_duration(
        self,
        page: Page,
        duration: int,
    ) -> None:

        control = (
            self._find_duration_control(
                page
            )
        )

        current = int(
            control.input_value()
        )

        minimum = int(
            control.get_attribute(
                "min"
            )
            or "0"
        )

        maximum = int(
            control.get_attribute(
                "max"
            )
            or "0"
        )

        step = int(
            control.get_attribute(
                "step"
            )
            or "1"
        )

        if (
            duration < minimum
            or duration > maximum
        ):
            raise ValueError(
                f"Ayvens duration {duration} "
                f"outside range "
                f"{minimum}-{maximum}"
            )

        if (
            (duration - minimum)
            % step
            != 0
        ):
            raise ValueError(
                f"Ayvens duration {duration} "
                f"does not match step "
                f"{step}"
            )

        if current != duration:

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
                duration,
            )

        page.wait_for_timeout(
            700
        )

        observed = int(
            control.input_value()
        )

        if observed != duration:
            raise ValueError(
                f"Ayvens duration selection failed: "
                f"requested={duration}, "
                f"observed={observed}"
            )

    # ============================================================
    # SELECT MILEAGE
    # ============================================================

    def _select_mileage(
        self,
        page: Page,
        mileage: int,
    ) -> None:

        control = (
            self._find_mileage_control(
                page
            )
        )

        current = int(
            control.input_value()
        )

        minimum = int(
            control.get_attribute(
                "min"
            )
            or "0"
        )

        maximum = int(
            control.get_attribute(
                "max"
            )
            or "0"
        )

        step = int(
            control.get_attribute(
                "step"
            )
            or "1"
        )

        if (
            mileage < minimum
            or mileage > maximum
        ):
            raise ValueError(
                f"Ayvens mileage {mileage} "
                f"outside range "
                f"{minimum}-{maximum}"
            )

        if (
            (mileage - minimum)
            % step
            != 0
        ):
            raise ValueError(
                f"Ayvens mileage {mileage} "
                f"does not match step "
                f"{step}"
            )

        if current != mileage:

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
                mileage,
            )

        page.wait_for_timeout(
            700
        )

        observed = int(
            control.input_value()
        )

        if observed != mileage:
            raise ValueError(
                f"Ayvens mileage selection failed: "
                f"requested={mileage}, "
                f"observed={observed}"
            )

    # ============================================================
    # SELECT COMPLETE CONTRACT
    # ============================================================

    def select_contract(
        self,
        page: Page,
        duration: int,
        mileage: int,
    ) -> None:

        print(
            f"Ayvens selecting contract: "
            f"{duration} hó / "
            f"{mileage:,} km"
        )

        self._select_duration(
            page,
            duration,
        )

        self._select_mileage(
            page,
            mileage,
        )

        # Az Ayvens Vue komponense időnként
        # még frissíti a havidíjat.
        page.wait_for_timeout(
            1000
        )

        observed_duration = (
            self.parse_duration(
                page
            )
        )

        observed_mileage = (
            self.parse_mileage(
                page
            )
        )

        if (
            observed_duration
            != duration
        ):
            raise ValueError(
                "Ayvens contract validation failed "
                f"(duration): requested="
                f"{duration}, "
                f"observed="
                f"{observed_duration}"
            )

        if (
            observed_mileage
            != mileage
        ):
            raise ValueError(
                "Ayvens contract validation failed "
                f"(mileage): requested="
                f"{mileage}, "
                f"observed="
                f"{observed_mileage}"
            )

        print(
            f"Ayvens contract selected: "
            f"{observed_duration} hó / "
            f"{observed_mileage:,} km"
        )

    # ============================================================
    # DISCOVER AVAILABLE CONTRACTS
    # ============================================================

    def discover_contracts(
        self,
        page: Page,
    ) -> list[tuple[int, int]]:

        contracts = []

        duration_control = (
            self._find_duration_control(
                page
            )
        )

        mileage_control = (
            self._find_mileage_control(
                page
            )
        )

        duration_min = int(
            duration_control.get_attribute(
                "min"
            )
            or "0"
        )

        duration_max = int(
            duration_control.get_attribute(
                "max"
            )
            or "0"
        )

        duration_step = int(
            duration_control.get_attribute(
                "step"
            )
            or "1"
        )

        mileage_min = int(
            mileage_control.get_attribute(
                "min"
            )
            or "0"
        )

        mileage_max = int(
            mileage_control.get_attribute(
                "max"
            )
            or "0"
        )

        mileage_step = int(
            mileage_control.get_attribute(
                "step"
            )
            or "1"
        )

        durations = list(
            range(
                duration_min,
                duration_max + 1,
                duration_step,
            )
        )

        mileages = list(
            range(
                mileage_min,
                mileage_max + 1,
                mileage_step,
            )
        )

        print(
            f"Ayvens duration range: "
            f"{duration_min}-{duration_max}, "
            f"step={duration_step}"
        )

        print(
            f"Ayvens mileage range: "
            f"{mileage_min}-{mileage_max}, "
            f"step={mileage_step}"
        )

        for duration in durations:

            for mileage in mileages:

                try:

                    self.select_contract(
                        page,
                        duration,
                        mileage,
                    )

                    contracts.append(
                        (
                            duration,
                            mileage,
                        )
                    )

                except Exception as e:

                    print(
                        f"⚠️ Ayvens contract "
                        f"not available: "
                        f"{duration} hó / "
                        f"{mileage:,} km"
                    )

                    print(
                        f"   {e}"
                    )

        return contracts
