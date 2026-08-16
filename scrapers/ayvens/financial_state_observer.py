from dataclasses import dataclass
import re
from typing import Optional

from playwright.sync_api import Page


@dataclass(frozen=True)
class AyvensFinancialState:
    switch_checked: bool
    down_payment_percent: float
    monthly_fee: int
    duration: Optional[int]
    mileage: Optional[int]
    source_url: str
    source_text: str


@dataclass(frozen=True)
class AyvensFinancialObservation:
    with_initial_payment: AyvensFinancialState
    without_initial_payment: AyvensFinancialState


class AyvensFinancialStateObserver:
    """
    Ayvens Financial State Observer V1.

    Observed UI semantics confirmed for the current Ayvens offer UI:
    - switch aria-checked=true  -> "Induló befizetés" enabled -> 20%
    - switch aria-checked=false -> "Induló befizetés" disabled -> 0%

    The monthly fee is NEVER calculated from the other state. Both fees
    must be directly observed after switching the provider UI.
    """

    LABEL = "Induló befizetés"

    def observe(self, page: Page) -> AyvensFinancialObservation:
        switch = self._resolve_switch(page)

        initial_checked = self._checked(switch)

        first = self._snapshot(
            page,
            switch,
        )

        switch.click(timeout=5000)
        page.wait_for_timeout(1500)

        second = self._snapshot(
            page,
            switch,
        )

        if first.switch_checked == second.switch_checked:
            raise ValueError(
                "Ayvens down-payment switch state did not change."
            )

        by_checked = {
            first.switch_checked: first,
            second.switch_checked: second,
        }

        if True not in by_checked or False not in by_checked:
            raise ValueError(
                "Both Ayvens financial switch states were not observed."
            )

        # Restore page to its initial state so this observer does not leave
        # hidden side effects for callers.
        if self._checked(switch) != initial_checked:
            switch.click(timeout=5000)
            page.wait_for_timeout(700)

        return AyvensFinancialObservation(
            with_initial_payment=by_checked[True],
            without_initial_payment=by_checked[False],
        )

    def _snapshot(
        self,
        page: Page,
        switch,
    ) -> AyvensFinancialState:
        checked = self._checked(switch)
        container = self._offer_panel(page)

        text = " ".join(
            container.inner_text().split()
        )

        monthly_fee = self._parse_monthly_fee(text)
        duration = self._parse_duration(text)
        mileage = self._parse_mileage(text)

        return AyvensFinancialState(
            switch_checked=checked,
            down_payment_percent=20.0 if checked else 0.0,
            monthly_fee=monthly_fee,
            duration=duration,
            mileage=mileage,
            source_url=page.url,
            source_text=text,
        )

    def _resolve_switch(self, page: Page):
        label = page.get_by_text(
            self.LABEL,
            exact=True,
        )

        if label.count() == 0:
            raise ValueError(
                "Ayvens 'Induló befizetés' label not found."
            )

        # The current PrimeVue DOM exposes a visible input[role=switch]
        # in the same compact offer configuration area.
        current = label.first

        for _ in range(5):
            parent = current.locator("xpath=..")

            if parent.count() == 0:
                break

            switches = parent.locator(
                "input[role='switch'], "
                "[role='switch'], "
                "input[type='checkbox']"
            )

            for i in range(switches.count()):
                candidate = switches.nth(i)

                try:
                    if candidate.is_visible():
                        return candidate
                except Exception:
                    continue

            current = parent

        raise ValueError(
            "Ayvens down-payment switch could not be resolved."
        )

    def _offer_panel(self, page: Page):
        label = page.get_by_text(
            self.LABEL,
            exact=True,
        ).first

        current = label

        # Climb to the smallest container that contains both the label
        # and the current monthly fee / contract terms.
        for _ in range(7):
            parent = current.locator("xpath=..")

            if parent.count() == 0:
                break

            try:
                text = " ".join(
                    parent.inner_text().split()
                )
            except Exception:
                current = parent
                continue

            if (
                "Ft / hó" in text
                and ("hónap" in text or "hó" in text)
                and "km/év" in text
            ):
                return parent

            current = parent

        raise ValueError(
            "Ayvens offer panel containing price and contract terms not found."
        )

    @staticmethod
    def _checked(switch) -> bool:
        value = switch.get_attribute(
            "aria-checked"
        )

        if value == "true":
            return True

        if value == "false":
            return False

        try:
            return bool(
                switch.is_checked()
            )
        except Exception:
            raise ValueError(
                "Ayvens financial switch checked state is not observable."
            )

    @staticmethod
    def _parse_monthly_fee(text: str) -> int:
        match = re.search(
            r"(\d{1,3}(?:[.\s]\d{3})+|\d{4,9})"
            r"\s*Ft\s*/\s*hó",
            text,
            re.IGNORECASE,
        )

        if not match:
            raise ValueError(
                "Ayvens monthly fee not found in offer panel."
            )

        return int(
            re.sub(
                r"\D",
                "",
                match.group(1),
            )
        )

    @staticmethod
    def _parse_duration(text: str) -> Optional[int]:
        match = re.search(
            r"(?<!\d)(\d{2})\s*hónap",
            text,
            re.IGNORECASE,
        )

        return (
            int(match.group(1))
            if match
            else None
        )

    @staticmethod
    def _parse_mileage(text: str) -> Optional[int]:
        match = re.search(
            r"(\d{1,3}(?:[.\s]\d{3})+|\d{4,6})"
            r"\s*km\s*/\s*év",
            text,
            re.IGNORECASE,
        )

        if not match:
            return None

        return int(
            re.sub(
                r"\D",
                "",
                match.group(1),
            )
        )
