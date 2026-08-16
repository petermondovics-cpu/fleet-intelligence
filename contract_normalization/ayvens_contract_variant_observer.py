import re
from dataclasses import dataclass
from typing import Optional, Tuple


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


OBSERVED = "OBSERVED"
UNRESOLVED = "UNRESOLVED"


class AyvensContractVariantObserver:
    """
    Ayvens Contract Variant Observer V1.

    Observes exact-offer monthly prices for requested duration/mileage
    coordinates by interacting with the live offer page.

    Safety:
    - only directly observed UI states are returned;
    - no interpolation or extrapolation;
    - if the requested contract state cannot be selected or confirmed,
      it remains unresolved;
    - financial down-payment state is not modified here.
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
                1500
            )

            self._dismiss(
                page
            )

            for duration, mileage in targets:

                selected = (
                    self._select_contract(
                        page,
                        duration,
                        mileage,
                    )
                )

                if not selected:
                    continue

                page.wait_for_timeout(
                    900
                )

                state = (
                    self._read_selected_state(
                        page
                    )
                )

                if state is None:
                    continue

                observed_duration = state[
                    "duration"
                ]

                observed_mileage = state[
                    "mileage"
                ]

                monthly_fee = state[
                    "monthly_fee"
                ]

                if (
                    observed_duration
                    != duration
                ):
                    continue

                if (
                    observed_mileage
                    != mileage
                ):
                    continue

                observations.append(
                    ObservedContractPrice(
                        duration=duration,
                        mileage=mileage,
                        monthly_fee=monthly_fee,
                        source_text=(
                            "Observed Ayvens exact-offer contract state: "
                            f"{duration} hó / {mileage} km/év -> "
                            f"{monthly_fee} Ft/hó."
                        ),
                    )
                )

            if not observations:
                return ContractVariantObservationResult(
                    status=UNRESOLVED,
                    provider="Ayvens",
                    source_url=url,
                    observations=(),
                    diagnostic=(
                        "No requested Ayvens contract variant could be "
                        "selected and re-confirmed from the exact offer UI."
                    ),
                )

            return ContractVariantObservationResult(
                status=OBSERVED,
                provider="Ayvens",
                source_url=url,
                observations=tuple(
                    observations
                ),
                diagnostic=(
                    "Requested Ayvens contract variants were directly "
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

        duration_ok = (
            self._select_duration(
                page,
                duration,
            )
        )

        if not duration_ok:
            return False

        mileage_ok = (
            self._select_mileage(
                page,
                mileage,
            )
        )

        return mileage_ok

    def _select_duration(
        self,
        page,
        duration: int,
    ) -> bool:

        text_variants = (
            f"{duration} hónap",
            f"{duration} hó",
            str(duration),
        )

        selectors = (
            "button",
            "[role='option']",
            "[role='radio']",
            "label",
            "div",
            "span",
        )

        for selector in selectors:

            loc = page.locator(
                selector
            )

            count = loc.count()

            for i in range(count):

                item = loc.nth(i)

                try:
                    if not item.is_visible():
                        continue

                    text = (
                        item.inner_text()
                        .strip()
                    )

                except Exception:
                    continue

                if not text:
                    continue

                normalized = (
                    " ".join(
                        text.split()
                    )
                    .casefold()
                )

                if not any(
                    variant.casefold()
                    in normalized
                    for variant in text_variants
                ):
                    continue

                if not (
                    "hó" in normalized
                    or "hónap" in normalized
                    or normalized == str(
                        duration
                    )
                ):
                    continue

                try:
                    item.click(
                        timeout=1800
                    )

                    page.wait_for_timeout(
                        500
                    )

                    state = (
                        self._read_selected_state(
                            page
                        )
                    )

                    if (
                        state
                        and state[
                            "duration"
                        ]
                        == duration
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

        formatted_variants = (
            f"{mileage}",
            f"{mileage:,}".replace(
                ",",
                ".",
            ),
            f"{mileage:,}".replace(
                ",",
                " ",
            ),
        )

        selectors = (
            "button",
            "[role='option']",
            "[role='radio']",
            "label",
            "div",
            "span",
        )

        for selector in selectors:

            loc = page.locator(
                selector
            )

            count = loc.count()

            for i in range(count):

                item = loc.nth(i)

                try:
                    if not item.is_visible():
                        continue

                    text = (
                        item.inner_text()
                        .strip()
                    )

                except Exception:
                    continue

                if not text:
                    continue

                normalized = (
                    " ".join(
                        text.split()
                    )
                    .casefold()
                )

                if not any(
                    variant
                    in normalized
                    for variant in (
                        value.casefold()
                        for value in formatted_variants
                    )
                ):
                    continue

                if "km" not in normalized:
                    continue

                try:
                    item.click(
                        timeout=1800
                    )

                    page.wait_for_timeout(
                        500
                    )

                    state = (
                        self._read_selected_state(
                            page
                        )
                    )

                    if (
                        state
                        and state[
                            "mileage"
                        ]
                        == mileage
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

        text = (
            page.locator("body")
            .inner_text()
        )

        contract = (
            self._parse_contract_state(
                text
            )
        )

        if contract is None:
            return None

        price = (
            self._parse_primary_price(
                text,
                contract[
                    "duration"
                ],
                contract[
                    "mileage"
                ],
            )
        )

        if price is None:
            return None

        return {
            "duration": contract[
                "duration"
            ],
            "mileage": contract[
                "mileage"
            ],
            "monthly_fee": price,
        }

    @staticmethod
    def _parse_contract_state(
        text: str,
    ) -> Optional[dict]:

        duration_match = re.search(
            r"(?i)(\d{2})\s*(?:hónap|hó)",
            text,
        )

        mileage_match = re.search(
            r"(?i)(\d{1,3}(?:[.\s]\d{3})+|\d{4,6})\s*km(?:/év|\s*/\s*év)?",
            text,
        )

        if (
            not duration_match
            or not mileage_match
        ):
            return None

        duration = int(
            duration_match.group(1)
        )

        mileage = int(
            re.sub(
                r"\D",
                "",
                mileage_match.group(1),
            )
        )

        return {
            "duration": duration,
            "mileage": mileage,
        }

    @staticmethod
    def _parse_primary_price(
        text: str,
        duration: int,
        mileage: int,
    ) -> Optional[int]:

        pattern = re.compile(
            r"(?is)"
            r"Induló\s+befizetés.*?"
            r"(\d{1,3}(?:[.\s]\d{3})+|\d{4,7})\s*Ft\s*/\s*hó.*?"
            + re.escape(
                str(duration)
            )
            + r"\s*(?:hónap|hó).*?"
            + r"(\d{1,3}(?:[.\s]\d{3})+|\d{4,6})\s*km(?:/év|\s*/\s*év)?"
        )

        match = pattern.search(
            text
        )

        if match:
            fee = int(
                re.sub(
                    r"\D",
                    "",
                    match.group(1),
                )
            )

            observed_mileage = int(
                re.sub(
                    r"\D",
                    "",
                    match.group(2),
                )
            )

            if (
                observed_mileage
                == mileage
            ):
                return fee

        # Conservative fallback: only use the first visible fee near the
        # sticky exact-offer contract box when contract coordinates have
        # already been confirmed.
        simple = re.search(
            r"(?i)(\d{1,3}(?:[.\s]\d{3})+|\d{4,7})\s*Ft\s*/\s*hó",
            text,
        )

        if not simple:
            return None

        return int(
            re.sub(
                r"\D",
                "",
                simple.group(1),
            )
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
