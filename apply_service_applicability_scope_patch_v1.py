from pathlib import Path
import re

ARVAL_PATH = Path("scrapers/arval/acquisition_connector.py")
AYVENS_PATH = Path("scrapers/ayvens/acquisition_connector.py")

ARVAL_METHOD = '    def service_discovery(self, task):\n        # Arval service acquisition scope V1.\n        # Current SERVICE_URLS are provider-level documentation, not the\n        # exact vehicle offer page. Keep them generic.\n        assertions = []\n        source_lines = []\n        source_url = None\n\n        for url in self.SERVICE_URLS:\n            page = self.browser.new_page()\n\n            try:\n                page.goto(\n                    url,\n                    wait_until="domcontentloaded",\n                    timeout=60000,\n                )\n                page.wait_for_timeout(1000)\n                self._dismiss(page)\n\n                text = page.locator("body").inner_text()\n                found = self._parse_services(text)\n\n                if found:\n                    source_url = source_url or url\n\n                    for item in found:\n                        if item not in assertions:\n                            assertions.append(item)\n\n                    source_lines.extend(\n                        item["source_text"]\n                        for item in found\n                    )\n\n            except Exception:\n                continue\n\n            finally:\n                page.close()\n\n        if not assertions:\n            return None\n\n        return {\n            "source_type": "PROVIDER_SERVICE_PAGE",\n            "source_url": source_url,\n            "source_text": " | ".join(source_lines),\n            "services": assertions,\n            "applicability_scope": "GENERIC_PROVIDER_DOCUMENTATION",\n        }\n\n'
AYVENS_METHOD = '    def service_discovery(self, task):\n        # Ayvens service acquisition scope V1.\n        # Check exact current offer first and never mix generic documentation\n        # into an EXACT_OFFER payload.\n        current_url = getattr(task, "current_url", None)\n\n        if current_url:\n            page = self.browser.new_page()\n\n            try:\n                page.goto(\n                    current_url,\n                    wait_until="domcontentloaded",\n                    timeout=60000,\n                )\n                page.wait_for_timeout(1000)\n                self._dismiss(page)\n\n                text = page.locator("body").inner_text()\n                found = self._parse_services(text)\n\n                if found:\n                    return {\n                        "source_type": "PROVIDER_OFFER_PAGE",\n                        "source_url": current_url,\n                        "source_text": " | ".join(\n                            item["source_text"]\n                            for item in found\n                        ),\n                        "services": found,\n                        "applicability_scope": "EXACT_OFFER",\n                    }\n\n            except Exception:\n                pass\n\n            finally:\n                page.close()\n\n        assertions = []\n        snippets = []\n        first_url = None\n\n        for url in self._unique(self.SERVICE_URLS):\n            page = self.browser.new_page()\n\n            try:\n                page.goto(\n                    url,\n                    wait_until="domcontentloaded",\n                    timeout=60000,\n                )\n                page.wait_for_timeout(1000)\n                self._dismiss(page)\n\n                text = page.locator("body").inner_text()\n                found = self._parse_services(text)\n\n                if not found:\n                    continue\n\n                first_url = first_url or url\n\n                existing = {\n                    item["code"]\n                    for item in assertions\n                }\n\n                for item in found:\n                    if item["code"] not in existing:\n                        assertions.append(item)\n                        existing.add(item["code"])\n                        snippets.append(item["source_text"])\n\n            except Exception:\n                continue\n\n            finally:\n                page.close()\n\n        if not assertions:\n            return None\n\n        return {\n            "source_type": "PROVIDER_SERVICE_PAGE",\n            "source_url": first_url,\n            "source_text": " | ".join(snippets),\n            "services": assertions,\n            "applicability_scope": "GENERIC_PROVIDER_DOCUMENTATION",\n        }\n\n'

def replace_method(path, method_text):
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"(?ms)^    def service_discovery\(self, task\):.*?"
        r"(?=^    def _discover_offer_urls\(self\):)"
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(
            f"{path}: expected one service_discovery block, found {len(matches)}"
        )

    backup = path.with_suffix(path.suffix + ".pre_service_scope_v1")
    backup.write_text(text, encoding="utf-8")

    updated = pattern.sub(method_text, text, count=1)
    path.write_text(updated, encoding="utf-8")
    compile(updated, str(path), "exec")

    print("PATCHED:", path)
    print("BACKUP :", backup)

def main():
    replace_method(ARVAL_PATH, ARVAL_METHOD)
    replace_method(AYVENS_PATH, AYVENS_METHOD)
    print("\nSERVICE APPLICABILITY SCOPE PATCH V1 APPLIED")

if __name__ == "__main__":
    main()
