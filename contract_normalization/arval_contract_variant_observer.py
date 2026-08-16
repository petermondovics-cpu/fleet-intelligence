import re
from dataclasses import dataclass
from typing import Optional, Tuple


OBSERVED = "OBSERVED"
UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class ObservedContractPrice:
    duration: int
    mileage: int
    monthly_fee: int
    source_text: str


@dataclass(frozen=True)
class ContractVariantObservationResult:
    status: str
    provider: str
    source_url: str
    observations: Tuple[ObservedContractPrice, ...]
    diagnostic: str


class ArvalContractVariantObserver:
    """
    Arval Contract Variant Observer V1.

    Observes exact-offer monthly prices for requested duration/mileage
    coordinates by interacting with the live Arval offer page.

    Safety:
    - only directly observed UI states are returned;
    - no interpolation, extrapolation or duration-price estimation;
    - a target is accepted only if duration + mileage can be re-read from
      the resulting page state;
    - failure to expose a requested state remains UNRESOLVED.
    """

    def __init__(
        self,
        browser,
    ):
        self.browser = browser

    def observe(
        self,
        url: str,
        targets: Tuple[
            Tuple[int, int],
            ...
        ],
    ) -> ContractVariantObservationResult:

        page = self.browser.new_page()
        observations = []

        try:
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            page.wait_for_timeout(
                1800
            )

            self._dismiss(
                page
            )

            for duration, mileage in targets:

                selected = self._select_contract(
                    page,
                    duration,
                    mileage,
                )

                if not selected:
                    continue

                page.wait_for_timeout(
                    900
                )

                state = self._read_selected_state(
                    page
                )

                if state is None:
                    continue

                if state["duration"] != duration:
                    continue

                if state["mileage"] != mileage:
                    continue

                observations.append(
                    ObservedContractPrice(
                        duration=duration,
                        mileage=mileage,
                        monthly_fee=state["monthly_fee"],
                        source_text=(
                            "Observed Arval exact-offer contract state: "
                            f"{duration} hó / {mileage} km/év -> "
                            f"{state['monthly_fee']} Ft/hó."
                        ),
                    )
                )

            if not observations:
                return ContractVariantObservationResult(
                    status=UNRESOLVED,
                    provider="Arval",
                    source_url=url,
                    observations=(),
                    diagnostic=(
                        "No requested Arval contract variant could be "
                        "selected and re-confirmed from the exact offer UI."
                    ),
                )

            return ContractVariantObservationResult(
                status=OBSERVED,
                provider="Arval",
                source_url=url,
                observations=tuple(observations),
                diagnostic=(
                    "Requested Arval contract variants were directly "
                    "observed on the exact offer page."
                ),
            )

        finally:
            page.close()

    # ========================================================
    # CONTRACT SELECTION
    # ========================================================

    def _select_contract(
        self,
        page,
        duration: int,
        mileage: int,
    ) -> bool:

        # First try controls that already expose a full contract coordinate.
        if self._select_combined_contract(
            page,
            duration,
            mileage,
        ):
            return True

        # Otherwise select duration and mileage independently.
        if not self._select_duration(
            page,
            duration,
        ):
            return False

        if not self._select_mileage(
            page,
            mileage,
        ):
            return False

        state = self._read_selected_state(
            page
        )

        return bool(
            state
            and state["duration"] == duration
            and state["mileage"] == mileage
        )

    def _select_combined_contract(
        self,
        page,
        duration: int,
        mileage: int,
    ) -> bool:

        selectors = (
            "p.OfferConfigurationTitle",
            "button",
            "[role='option']",
            "[role='radio']",
            "[role='button']",
            "label",
        )

        for selector in selectors:

            loc = page.locator(
                selector
            )

            for i in range(
                loc.count()
            ):

                item = loc.nth(i)

                try:
                    if not item.is_visible():
                        continue

                    text = " ".join(
                        item.inner_text()
                        .split()
                    )

                except Exception:
                    continue

                if not self._text_has_duration(
                    text,
                    duration,
                ):
                    continue

                if not self._text_has_mileage(
                    text,
                    mileage,
                ):
                    continue

                try:
                    item.click(
                        timeout=1800
                    )

                    page.wait_for_timeout(
                        600
                    )

                    state = self._read_selected_state(
                        page
                    )

                    if (
                        state
                        and state["duration"] == duration
                        and state["mileage"] == mileage
                    ):
                        return True

                except Exception:
                    continue

        return False

    def _select_duration(
        self,
        page,
        duration: int,
    ) -> bool:

        selectors = (
            "p.OfferConfigurationTitle",
            "button",
            "[role='option']",
            "[role='radio']",
            "[role='button']",
            "label",
            "span",
            "div",
        )

        for selector in selectors:

            loc = page.locator(
                selector
            )

            for i in range(
                loc.count()
            ):

                item = loc.nth(i)

                try:
                    if not item.is_visible():
                        continue

                    text = " ".join(
                        item.inner_text()
                        .split()
                    )

                except Exception:
                    continue

                if not self._text_has_duration(
                    text,
                    duration,
                ):
                    continue

                try:
                    item.click(
                        timeout=1800
                    )

                    page.wait_for_timeout(
                        500
                    )

                    state = self._read_selected_state(
                        page
                    )

                    if (
                        state
                        and state["duration"] == duration
                    ):
                        return True

                except Exception:
                    continue

        return False

    def _select_mileage(
        self,
        page,
        mileage: int,
    ) -> bool:

        selectors = (
            "p.OfferConfigurationTitle",
            "button",
            "[role='option']",
            "[role='radio']",
            "[role='button']",
            "label",
            "span",
            "div",
        )

        for selector in selectors:

            loc = page.locator(
                selector
            )

            for i in range(
                loc.count()
            ):

                item = loc.nth(i)

                try:
                    if not item.is_visible():
                        continue

                    text = " ".join(
                        item.inner_text()
                        .split()
                    )

                except Exception:
                    continue

                if not self._text_has_mileage(
                    text,
                    mileage,
                ):
                    continue

                try:
                    item.click(
                        timeout=1800
                    )

                    page.wait_for_timeout(
                        500
                    )

                    state = self._read_selected_state(
                        page
                    )

                    if (
                        state
                        and state["mileage"] == mileage
                    ):
                        return True

                except Exception:
                    continue

        return False

    # ========================================================
    # STATE READING
    # ========================================================

    def _read_selected_state(
        self,
        page,
    ) -> Optional[dict]:

        text = page.locator(
            "body"
        ).inner_text()

        duration = self._parse_duration(
            text
        )

        mileage = self._parse_mileage(
            text
        )

        if (
            duration is None
            or mileage is None
        ):
            return None

        fee = self._parse_primary_price(
            text,
            duration,
            mileage,
        )

        if fee is None:
            return None

        return {
            "duration": duration,
            "mileage": mileage,
            "monthly_fee": fee,
        }

    @staticmethod
    def _parse_duration(
        text: str,
    ) -> Optional[int]:

        patterns = (
            r"(?i)(\d{2})\s*(?:hónap|hó)\b",
            r"(?i)futamidő[^0-9]{0,40}(\d{2})",
        )

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
            )

            if not match:
                continue

            value = int(
                match.group(1)
            )

            if 12 <= value <= 84:
                return value

        return None

    @staticmethod
    def _parse_mileage(
        text: str,
    ) -> Optional[int]:

        patterns = (
            r"(?i)(\d{1,3}(?:[.\s,]\d{3})+|\d{4,6})\s*km\s*/?\s*év",
            r"(?i)futásteljesítmény[^0-9]{0,60}"
            r"(\d{1,3}(?:[.\s,]\d{3})+|\d{4,6})",
        )

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
            )

            if not match:
                continue

            value = int(
                re.sub(
                    r"\D",
                    "",
                    match.group(1),
                )
            )

            if 5000 <= value <= 100000:
                return value

        return None

    @staticmethod
    def _parse_primary_price(
        text: str,
        duration: int,
        mileage: int,
    ) -> Optional[int]:

        # Prefer a fee close to the observed contract coordinates.
        coordinate_pattern = re.compile(
            r"(?is)"
            r"(\d{1,3}(?:[.\s]\d{3})+|\d{4,7})\s*Ft"
            r".{0,300}?"
            + re.escape(str(duration))
            + r"\s*(?:hónap|hó)"
            r".{0,300}?"
            r"(\d{1,3}(?:[.\s]\d{3})+|\d{4,6})\s*km\s*/?\s*év"
        )

        for match in coordinate_pattern.finditer(
            text
        ):

            observed_mileage = int(
                re.sub(
                    r"\D",
                    "",
                    match.group(2),
                )
            )

            if observed_mileage != mileage:
                continue

            return int(
                re.sub(
                    r"\D",
                    "",
                    match.group(1),
                )
            )

        # Conservative fallback: first monthly fee only after duration
        # and mileage have already been re-confirmed from the same page.
        patterns = (
            r"(?i)(\d{1,3}(?:[.\s]\d{3})+|\d{4,7})\s*Ft\s*/\s*hó",
            r"(?i)nettó[^0-9]{0,20}"
            r"(\d{1,3}(?:[.\s]\d{3})+|\d{4,7})\s*Ft",
        )

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
            )

            if match:
                return int(
                    re.sub(
                        r"\D",
                        "",
                        match.group(1),
                    )
                )

        return None

    # ========================================================
    # TEXT HELPERS
    # ========================================================

    @staticmethod
    def _text_has_duration(
        text: str,
        duration: int,
    ) -> bool:

        normalized = " ".join(
            (text or "").split()
        ).casefold()

        return bool(
            re.search(
                rf"(?<!\d){duration}\s*(?:hónap|hó)\b",
                normalized,
            )
        )

    @staticmethod
    def _text_has_mileage(
        text: str,
        mileage: int,
    ) -> bool:

        normalized = " ".join(
            (text or "").split()
        ).casefold()

        digits = re.sub(
            r"\D",
            "",
            normalized,
        )

        return (
            str(mileage) in digits
            and "km" in normalized
        )

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _dismiss(
        page,
    ):
        for selector in (
            "#onetrust-reject-all-handler",
            "#onetrust-accept-btn-handler",
            "button:has-text('Összes elfogadása')",
            "button:has-text('Elfogadom')",
            "button:has-text('Elutasítom')",
        ):
            loc = page.locator(
                selector
            )

            if loc.count() == 0:
                continue

            try:
                loc.first.click(
                    timeout=1500
                )

                page.wait_for_timeout(
                    200
                )

                return

            except Exception:
                pass
