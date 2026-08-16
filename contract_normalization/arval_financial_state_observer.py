import re
from dataclasses import dataclass
from typing import Optional, Tuple


OBSERVED = "OBSERVED"
UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class ObservedFinancialState:
    monthly_fee: int
    down_payment_percent: Optional[float]
    down_payment_amount_huf: Optional[int]
    duration: Optional[int]
    mileage: Optional[int]
    source_text: str


@dataclass(frozen=True)
class FinancialStateObservationResult:
    status: str
    provider: str
    source_url: str
    states: Tuple[ObservedFinancialState, ...]
    diagnostic: str


class ArvalFinancialStateObserver:
    """
    Arval Financial State Observer V2.

    Exact-offer financial observation with Arval-specific price parsing.

    Known Arval live wording:
        192312 FT +ÁFA / hónap
        Időtartam60 hónap
        Futásteljesítmény 20000 km/év

    Safety:
    - no assumed 20% down payment;
    - no assumed 0% down payment;
    - no calculation of down payment from monthly fee;
    - no inference from market practice;
    - absence of explicit DP wording remains UNKNOWN.
    """

    ZERO_DOWN_PATTERNS = (
        r"(?i)\b0\s*%\s*(?:kezdő|induló|első|önerő)",
        r"(?i)(?:kezdő|induló|első)\s+befizetés[^.\n]{0,50}\b0\s*%",
        r"(?i)\bönerő[^.\n]{0,50}\b0\s*%",
        r"(?i)\bkezdő\s+befizetés\s+nélkül\b",
        r"(?i)\bönerő\s+nélkül\b",
    )

    PERCENT_PATTERNS = (
        r"(?i)(?:kezdő|induló|első)\s+befizetés[^0-9%\n]{0,50}"
        r"(\d{1,3}(?:[.,]\d+)?)\s*%",
        r"(?i)\bönerő[^0-9%\n]{0,50}"
        r"(\d{1,3}(?:[.,]\d+)?)\s*%",
        r"(?i)(\d{1,3}(?:[.,]\d+)?)\s*%"
        r"[^.\n]{0,50}(?:kezdő|induló|első)\s+befizetés",
    )

    AMOUNT_PATTERNS = (
        r"(?i)(?:kezdő|induló|első)\s+befizetés[^0-9\n]{0,50}"
        r"(\d{1,3}(?:[.\s]\d{3})+|\d{4,9})\s*Ft",
        r"(?i)\bönerő[^0-9\n]{0,50}"
        r"(\d{1,3}(?:[.\s]\d{3})+|\d{4,9})\s*Ft",
    )

    def __init__(self, browser):
        self.browser = browser

    def observe(
        self,
        url: str,
    ) -> FinancialStateObservationResult:

        page = self.browser.new_page()

        try:
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(1800)
            self._dismiss(page)

            body = page.locator("body").inner_text()

            monthly_fee = self._parse_monthly_fee(body)
            duration = self._parse_duration(body)
            mileage = self._parse_mileage(body)

            if monthly_fee is None:
                return FinancialStateObservationResult(
                    status=UNRESOLVED,
                    provider="Arval",
                    source_url=url,
                    states=(),
                    diagnostic=(
                        "Exact-offer monthly fee could not be safely "
                        "re-read from the Arval page."
                    ),
                )

            financial = self._parse_explicit_down_payment(body)

            if financial is None:
                return FinancialStateObservationResult(
                    status=UNRESOLVED,
                    provider="Arval",
                    source_url=url,
                    states=(),
                    diagnostic=(
                        "Arval exact-offer monthly fee was directly "
                        f"observed as {monthly_fee} Ft/hó"
                        + (
                            f" at {duration} months / {mileage} km/year"
                            if duration is not None and mileage is not None
                            else ""
                        )
                        + ", but no explicit down-payment percentage, "
                        "amount, or zero-down statement was found. "
                        "Down payment remains UNKNOWN."
                    ),
                )

            percent, amount, evidence_text = financial

            state = ObservedFinancialState(
                monthly_fee=monthly_fee,
                down_payment_percent=percent,
                down_payment_amount_huf=amount,
                duration=duration,
                mileage=mileage,
                source_text=evidence_text,
            )

            return FinancialStateObservationResult(
                status=OBSERVED,
                provider="Arval",
                source_url=url,
                states=(state,),
                diagnostic=(
                    "Explicit Arval exact-offer financial condition "
                    "was directly observed."
                ),
            )

        finally:
            page.close()

    @classmethod
    def _parse_explicit_down_payment(
        cls,
        text: str,
    ):

        for pattern in cls.ZERO_DOWN_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return (
                    0.0,
                    0,
                    cls._excerpt(text, match.start(), match.end()),
                )

        for pattern in cls.PERCENT_PATTERNS:
            match = re.search(pattern, text)
            if not match:
                continue

            raw = match.group(1).replace(",", ".")

            try:
                percent = float(raw)
            except ValueError:
                continue

            if 0.0 <= percent <= 100.0:
                return (
                    percent,
                    None,
                    cls._excerpt(text, match.start(), match.end()),
                )

        for pattern in cls.AMOUNT_PATTERNS:
            match = re.search(pattern, text)
            if not match:
                continue

            amount = int(
                re.sub(r"\D", "", match.group(1))
            )

            if amount >= 0:
                return (
                    None,
                    amount,
                    cls._excerpt(text, match.start(), match.end()),
                )

        return None

    @staticmethod
    def _parse_monthly_fee(
        text: str,
    ) -> Optional[int]:

        # Arval current live format:
        #   192312 FT +ÁFA / hónap
        #
        # Keep generic alternatives too, but require an explicit
        # monthly-unit wording. Do not accept arbitrary FT values.
        patterns = (
            r"(?i)(\d{4,9})\s*FT\s*\+?\s*ÁFA\s*/\s*hónap\b",
            r"(?i)(\d{1,3}(?:[.\s]\d{3})+|\d{4,9})"
            r"\s*FT\s*(?:\+?\s*ÁFA\s*)?/\s*(?:hónap|hó)\b",
            r"(?i)(\d{1,3}(?:[.\s]\d{3})+|\d{4,9})"
            r"\s*Ft\s*/\s*hó\b",
            r"(?i)nettó[^0-9\n]{0,30}"
            r"(\d{1,3}(?:[.\s]\d{3})+|\d{4,9})\s*Ft",
        )

        for pattern in patterns:
            match = re.search(pattern, text)
            if not match:
                continue

            value = int(
                re.sub(r"\D", "", match.group(1))
            )

            if 10000 <= value <= 5000000:
                return value

        return None

    @staticmethod
    def _parse_duration(
        text: str,
    ) -> Optional[int]:

        patterns = (
            r"(?i)Időtartam\s*(\d{2})\s*hónap\b",
            r"(?i)(\d{2})\s*(?:hónap|hó)\b",
            r"(?i)futamidő[^0-9\n]{0,40}(\d{2})",
        )

        for pattern in patterns:
            match = re.search(pattern, text)
            if not match:
                continue

            value = int(match.group(1))

            if 12 <= value <= 84:
                return value

        return None

    @staticmethod
    def _parse_mileage(
        text: str,
    ) -> Optional[int]:

        patterns = (
            r"(?i)Futásteljesítmény\s*"
            r"(\d{1,3}(?:[.\s,]\d{3})+|\d{4,6})\s*km/év",
            r"(?i)(\d{1,3}(?:[.\s,]\d{3})+|\d{4,6})"
            r"\s*km\s*/?\s*év",
        )

        for pattern in patterns:
            match = re.search(pattern, text)
            if not match:
                continue

            value = int(
                re.sub(r"\D", "", match.group(1))
            )

            if 5000 <= value <= 100000:
                return value

        return None

    @staticmethod
    def _excerpt(
        text: str,
        start: int,
        end: int,
        radius: int = 100,
    ) -> str:

        lo = max(0, start - radius)
        hi = min(len(text), end + radius)

        return " ".join(
            text[lo:hi].split()
        )

    @staticmethod
    def _dismiss(page):
        for selector in (
            "#onetrust-reject-all-handler",
            "#onetrust-accept-btn-handler",
            "button:has-text('Összes elfogadása')",
            "button:has-text('Elfogadom')",
            "button:has-text('Elutasítom')",
        ):
            loc = page.locator(selector)

            if loc.count() == 0:
                continue

            try:
                loc.first.click(timeout=1500)
                page.wait_for_timeout(200)
                return
            except Exception:
                pass
