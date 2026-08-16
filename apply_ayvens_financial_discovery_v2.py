from pathlib import Path

PATH = Path("scrapers/ayvens/acquisition_connector.py")


NEW_METHOD = """    def financial_discovery(self, task):
        \"""
        Ayvens Financial Discovery V2.

        Uses the live financial switch observer on the exact current offer page.

        Observed UI semantics:
        - switch ON  -> 20% initial payment
        - switch OFF -> 0% initial payment

        The 0% state is the comparison baseline because it is directly observed
        and requires no assumed down payment. The 20% state is preserved in the
        payload as an observed alternate financial variant.

        No price is mathematically derived from the other state.
        \"""
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

"""


def main():
    text = PATH.read_text(encoding="utf-8")

    start = text.find("    def financial_discovery(self, task):")
    if start < 0:
        raise RuntimeError("financial_discovery() not found")

    end = text.find("    def service_discovery(self, task):", start)
    if end < 0:
        raise RuntimeError("service_discovery() marker not found")

    original = text[start:end]
    updated = text[:start] + NEW_METHOD + text[end:]

    compile(updated, str(PATH), "exec")

    backup = PATH.with_suffix(PATH.suffix + ".pre_financial_observer_v1")
    if not backup.exists():
        backup.write_text(text, encoding="utf-8")

    PATH.write_text(updated, encoding="utf-8")

    print("PATCHED:", PATH)
    print("BACKUP :", backup)
    print("AYVENS FINANCIAL DISCOVERY V2 APPLIED")


if __name__ == "__main__":
    main()
