import re
from typing import Optional


class AyvensAcquisitionConnector:
    """
    Ayvens Acquisition Connector V1.

    Callbacks for AcquisitionExecutor:
    - CONTRACT: discover a different observed PRICED Ayvens offer for the
      same canonical vehicle identity.
    - FINANCIAL: search explicit provider wording for down payment /
      initial payment.
    - SERVICES: collect explicit Ayvens service assertions.

    Critical safety barrier:
    Ayvens quote controls (duration 36-60 and mileage 20k-60k) are
    capability metadata only. They NEVER create priced contract evidence.
    Contract evidence must come from a separately observed advertised
    offer containing explicit monthly fee + duration + mileage.
    """

    LIST_URL = "https://autotartosberlet.ayvens.com/"

    SERVICE_URLS = (
        "https://autotartosberlet.ayvens.com/",
    )

    FINANCIAL_URLS = (
        "https://autotartosberlet.ayvens.com/",
    )

    def __init__(
        self,
        browser,
        *,
        canonical_key_builder,
    ):
        self.browser = browser
        self.canonical_key_builder = canonical_key_builder

    # ========================================================
    # EXECUTOR CALLBACKS
    # ========================================================

    def contract_discovery(self, task):
        target_key = task.canonical_vehicle_key
        current_duration = getattr(task, "current_duration", None)
        current_mileage = getattr(task, "current_mileage", None)
        target_duration = getattr(task, "target_duration", None)
        target_mileage = getattr(task, "target_mileage", None)
        current_url = getattr(task, "current_url", None)

        for url in self._discover_offer_urls():

            # Reopening the current page cannot establish a second
            # observed priced contract variant.
            if current_url and self._clean_url(url) == self._clean_url(current_url):
                continue

            page = self.browser.new_page()

            try:
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                page.wait_for_timeout(1200)
                self._dismiss(page)

                from scrapers.ayvens.evidence_aware_builder import (
                    AyvensEvidenceAwareBuilder,
                )

                wrapped = AyvensEvidenceAwareBuilder().build(page)

                if self.canonical_key_builder(wrapped) != target_key:
                    continue

                offer = wrapped.composite.offer

                # Target Contract Discovery V1:
                # accept only the exact endpoint required by this comparison.
                if (
                    target_duration is not None
                    and offer.duration != target_duration
                ):
                    continue

                if (
                    target_mileage is not None
                    and offer.mileage != target_mileage
                ):
                    continue

                # Backward-compatible safety when no explicit target exists.
                if (
                    target_duration is None
                    and target_mileage is None
                    and current_duration is not None
                    and current_mileage is not None
                    and offer.duration == current_duration
                    and offer.mileage == current_mileage
                ):
                    continue

                return {
                    "source_type": "PROVIDER_PRICED_OFFER_PAGE",
                    "source_url": offer.url,
                    "source_text": (
                        f"{offer.brand} {offer.model} {offer.trim}; "
                        f"{offer.duration} hó; {offer.mileage} km/év; "
                        f"{offer.monthly_fee} Ft/hó"
                    ),
                    "provider": offer.provider,
                    "brand": offer.brand,
                    "model": offer.model,
                    "trim": offer.trim,
                    "fuel_type": offer.fuel_type,
                    "monthly_fee": offer.monthly_fee,
                    "duration": offer.duration,
                    "mileage": offer.mileage,
                    # Explicitly record provenance: this came from the
                    # advertised contract, never from quote controls.
                    "pricing_basis": "ADVERTISED_CONTRACT",
                }

            except Exception:
                continue
            finally:
                page.close()

        return None

    def financial_discovery(self, task):
        """
        Ayvens Financial Discovery V2.

        Uses the live financial switch observer on the exact current offer page.

        Observed UI semantics:
        - switch ON  -> 20% initial payment
        - switch OFF -> 0% initial payment

        The 0% state is the comparison baseline because it is directly observed
        and requires no assumed down payment. The 20% state is preserved in the
        payload as an observed alternate financial variant.

        No price is mathematically derived from the other state.
        """
        current_url = getattr(task, "current_url", None)

        if current_url:
            page = self.browser.new_page()

            try:
                page.goto(
                    current_url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                page.wait_for_timeout(1800)
                self._dismiss(page)

                from scrapers.ayvens.financial_state_observer import (
                    AyvensFinancialStateObserver,
                )

                observation = (
                    AyvensFinancialStateObserver()
                    .observe(page)
                )

                with_dp = observation.with_initial_payment
                without_dp = observation.without_initial_payment

                if (
                    with_dp.duration != without_dp.duration
                    or with_dp.mileage != without_dp.mileage
                ):
                    return None

                return {
                    "source_type": "PROVIDER_OFFER_PAGE",
                    "source_url": current_url,
                    "source_text": (
                        f"Observed Ayvens financial switch states on exact offer: "
                        f"20% initial payment -> {with_dp.monthly_fee} Ft/hó; "
                        f"0% initial payment -> {without_dp.monthly_fee} Ft/hó; "
                        f"{without_dp.duration} hó; "
                        f"{without_dp.mileage} km/év."
                    ),
                    # Comparison baseline:
                    "down_payment_percent": 0.0,
                    "monthly_fee": without_dp.monthly_fee,
                    "duration": without_dp.duration,
                    "mileage": without_dp.mileage,
                    "pricing_basis": "OBSERVED_ZERO_DOWN_PAYMENT_STATE",
                    "applicability_scope": "EXACT_OFFER",
                    # Preserve the observed alternate state:
                    "financial_variants": (
                        {
                            "down_payment_percent": 20.0,
                            "monthly_fee": with_dp.monthly_fee,
                            "duration": with_dp.duration,
                            "mileage": with_dp.mileage,
                            "switch_checked": True,
                        },
                        {
                            "down_payment_percent": 0.0,
                            "monthly_fee": without_dp.monthly_fee,
                            "duration": without_dp.duration,
                            "mileage": without_dp.mileage,
                            "switch_checked": False,
                        },
                    ),
                }

            except Exception:
                pass

            finally:
                page.close()

        # Fallback: preserve existing text-parser discovery for any other
        # explicitly worded provider financial condition. Absence remains
        # unresolved and never becomes 0%.
        urls = list(self.FINANCIAL_URLS)

        for url in self._unique(urls):
            page = self.browser.new_page()

            try:
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                page.wait_for_timeout(1000)
                self._dismiss(page)

                text = page.locator("body").inner_text()
                parsed = self._parse_down_payment(text)

                if parsed is None:
                    continue

                result = {
                    "source_type": "PROVIDER_OFFER_PAGE",
                    "source_url": url,
                    "source_text": parsed["source_text"],
                }
                result.update(parsed["payload"])
                return result

            except Exception:
                continue

            finally:
                page.close()

        return None

    def service_discovery(self, task):
        # Ayvens service acquisition scope V1.
        # Check exact current offer first and never mix generic documentation
        # into an EXACT_OFFER payload.
        current_url = getattr(task, "current_url", None)

        if current_url:
            page = self.browser.new_page()

            try:
                page.goto(
                    current_url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                page.wait_for_timeout(1000)
                self._dismiss(page)

                text = page.locator("body").inner_text()
                found = self._parse_services(text)

                if found:
                    return {
                        "source_type": "PROVIDER_OFFER_PAGE",
                        "source_url": current_url,
                        "source_text": " | ".join(
                            item["source_text"]
                            for item in found
                        ),
                        "services": found,
                        "applicability_scope": "EXACT_OFFER",
                    }

            except Exception:
                pass

            finally:
                page.close()

        assertions = []
        snippets = []
        first_url = None

        for url in self._unique(self.SERVICE_URLS):
            page = self.browser.new_page()

            try:
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                page.wait_for_timeout(1000)
                self._dismiss(page)

                text = page.locator("body").inner_text()
                found = self._parse_services(text)

                if not found:
                    continue

                first_url = first_url or url

                existing = {
                    item["code"]
                    for item in assertions
                }

                for item in found:
                    if item["code"] not in existing:
                        assertions.append(item)
                        existing.add(item["code"])
                        snippets.append(item["source_text"])

            except Exception:
                continue

            finally:
                page.close()

        if not assertions:
            return None

        return {
            "source_type": "PROVIDER_SERVICE_PAGE",
            "source_url": first_url,
            "source_text": " | ".join(snippets),
            "services": assertions,
            "applicability_scope": "GENERIC_PROVIDER_DOCUMENTATION",
        }

    def _discover_offer_urls(self):
        page = self.browser.new_page()

        try:
            page.goto(
                self.LIST_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(1500)
            self._dismiss(page)

            urls = page.locator("a[href]").evaluate_all(
                """els => els.map(a => a.href).filter(
                    x => x && x.includes('autotartosberlet.ayvens.com/')
                )"""
            )

            out = []
            seen = set()

            for url in urls:
                clean = self._clean_url(url)

                # Detail pattern: /brand/model-slug
                path = clean.split("autotartosberlet.ayvens.com/", 1)[-1]
                parts = [p for p in path.split("/") if p]

                if len(parts) < 2:
                    continue

                if clean in seen:
                    continue

                seen.add(clean)
                out.append(clean)

            return out

        finally:
            page.close()

    # ========================================================
    # PARSERS
    # ========================================================

    @staticmethod
    def _parse_down_payment(text: str) -> Optional[dict]:
        patterns = (
            (
                r"(?i)(?:önerő|kezdő\s*bérleti\s*díj|induló\s*díj|"
                r"első\s*emelt\s*bérleti\s*díj)"
                r"[^%\n]{0,100}?(\d{1,3}(?:[.,]\d+)?)\s*%",
                "percent",
            ),
            (
                r"(?i)(\d{1,3}(?:[.,]\d+)?)\s*%"
                r"[^.\n]{0,100}?(?:önerő|kezdő\s*bérleti\s*díj|"
                r"induló\s*díj|első\s*emelt\s*bérleti\s*díj)",
                "percent",
            ),
            (
                r"(?i)(?:önerő|kezdő\s*bérleti\s*díj|induló\s*díj|"
                r"első\s*emelt\s*bérleti\s*díj)"
                r"[^0-9\n]{0,50}?([\d .]+)\s*(?:ft|forint)",
                "amount",
            ),
        )

        for pattern, kind in patterns:
            match = re.search(pattern, text)

            if not match:
                continue

            raw = match.group(1)

            if kind == "percent":
                value = float(raw.replace(",", "."))

                if 0 <= value <= 100:
                    return {
                        "source_text": match.group(0),
                        "payload": {
                            "down_payment_percent": value,
                        },
                    }
                continue

            digits = re.sub(r"\D", "", raw)

            if digits:
                return {
                    "source_text": match.group(0),
                    "payload": {
                        "down_payment_amount": int(digits),
                    },
                }

        return None

    @staticmethod
    def _parse_services(text: str):
        checks = (
            ("MAINTENANCE", (
                "teljes körű karbantartás",
                "karbantartás",
            )),
            ("TYRES", (
                "téli-, nyári gumiabroncs",
                "téli- és nyári gumiabroncs",
                "gumiabroncs",
            )),
            ("MOBILITY", (
                "assistance szolgáltatás",
                "assistance",
            )),
            ("ADMINISTRATION", (
                "myayvens online ügyintézési rendszer",
                "myayvens",
            )),
            ("TAXES", (
                "vonatkozó adók",
                "adók",
            )),
            ("INSURANCE", (
                "biztosítási csomag",
                "biztosítás",
            )),
        )

        lowered = text.casefold()
        found = []

        for code, aliases in checks:
            for alias in aliases:
                idx = lowered.find(alias.casefold())

                if idx < 0:
                    continue

                start = max(0, idx - 80)
                end = min(len(text), idx + len(alias) + 120)

                found.append({
                    "code": code,
                    "included": True,
                    "source_text": " ".join(text[start:end].split()),
                })
                break

        return found

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _clean_url(url):
        return url.split("?")[0].split("#")[0].rstrip("/")

    @staticmethod
    def _unique(values):
        out = []
        seen = set()

        for value in values:
            if not value:
                continue

            clean = AyvensAcquisitionConnector._clean_url(value)
            if clean in seen:
                continue

            seen.add(clean)
            out.append(clean)

        return out

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
