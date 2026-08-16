"""
Ayvens Equipment Parser V4 semantic fix.

Purpose
-------
Preserve the distinction between:
1. equipment control/panel genuinely absent -> NOT_PUBLISHED
2. equipment control or panel exists but contains no trustworthy items
   -> PARSING_UNRESOLVED
3. explicit trustworthy equipment items observed -> PUBLISHED

This patch is intended to replace the corresponding logic in
scrapers/ayvens/equipment_parser.py. Keep the existing extraction/recovery
helpers from V3; apply the semantic rules below to _parse_tab and _find_tab.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from playwright.sync_api import Page

from models.vehicle_specification import (
    EVIDENCE_OBSERVED,
    EquipmentItem,
    VehicleEvidence,
)

EQUIPMENT_PUBLISHED = "PUBLISHED"
EQUIPMENT_NOT_PUBLISHED = "NOT_PUBLISHED"
EQUIPMENT_PARSING_UNRESOLVED = "PARSING_UNRESOLVED"


@dataclass(frozen=True)
class EquipmentParseResult:
    status: str
    items: List[EquipmentItem]
    source_url: str
    tab_label: str
    diagnostic: str = ""

    @property
    def published(self) -> bool:
        return self.status == EQUIPMENT_PUBLISHED

    @property
    def item_count(self) -> int:
        return len(self.items)


class AyvensEquipmentParser:
    STANDARD_TAB = "Alapfelszereltség"
    OPTIONAL_TAB = "Beépített extra felszereltség"

    def parse_standard_equipment(self, page: Page) -> EquipmentParseResult:
        return self._parse_tab(page, self.STANDARD_TAB, standard=True)

    def parse_optional_equipment(self, page: Page) -> EquipmentParseResult:
        return self._parse_tab(page, self.OPTIONAL_TAB, standard=False)

    def _parse_tab(
        self,
        page: Page,
        tab_label: str,
        standard: bool,
    ) -> EquipmentParseResult:
        control, panel = self._find_control_and_panel(page, tab_label)

        # NOT_PUBLISHED is now reserved for genuine structural absence.
        if control is None and panel is None:
            return EquipmentParseResult(
                status=EQUIPMENT_NOT_PUBLISHED,
                items=[],
                source_url=page.url,
                tab_label=tab_label,
                diagnostic="Equipment control and panel are not present in the DOM.",
            )

        # If a visible tab/control exists, activate it when possible.
        if control is not None:
            try:
                control.scroll_into_view_if_needed()
            except Exception:
                pass

            try:
                if control.get_attribute("aria-selected") != "true":
                    control.click(timeout=5000)
                    page.wait_for_timeout(800)
            except Exception as exc:
                # Do not downgrade structural presence to NOT_PUBLISHED.
                return EquipmentParseResult(
                    status=EQUIPMENT_PARSING_UNRESOLVED,
                    items=[],
                    source_url=page.url,
                    tab_label=tab_label,
                    diagnostic=(
                        "Equipment control exists but could not be activated: "
                        f"{exc}"
                    ),
                )

            # Re-resolve after activation because PrimeVue may update nodes.
            _, refreshed_panel = self._find_control_and_panel(page, tab_label)
            if refreshed_panel is not None:
                panel = refreshed_panel

        if panel is None:
            return EquipmentParseResult(
                status=EQUIPMENT_PARSING_UNRESOLVED,
                items=[],
                source_url=page.url,
                tab_label=tab_label,
                diagnostic=(
                    "Equipment control/heading exists, but its content panel "
                    "could not be resolved."
                ),
            )

        texts = self._extract_items(panel, tab_label)

        if not texts:
            return EquipmentParseResult(
                status=EQUIPMENT_PARSING_UNRESOLVED,
                items=[],
                source_url=page.url,
                tab_label=tab_label,
                diagnostic=(
                    "Equipment panel exists, but contains no trustworthy "
                    "equipment leaf items."
                ),
            )

        items = [
            EquipmentItem(
                name=text,
                category="OTHER",
                included=True,
                standard=standard,
                evidence=VehicleEvidence(
                    status=EVIDENCE_OBSERVED,
                    source_url=page.url,
                    source_text=text,
                ),
            )
            for text in texts
        ]

        return EquipmentParseResult(
            status=EQUIPMENT_PUBLISHED,
            items=items,
            source_url=page.url,
            tab_label=tab_label,
            diagnostic=f"{len(items)} observed equipment items extracted.",
        )

    def _find_control_and_panel(
        self,
        page: Page,
        label: str,
    ) -> Tuple[Optional[object], Optional[object]]:
        """
        Resolve control and panel independently.

        Critical V4 rule:
        a hidden tabpanel is still evidence that the equipment section is
        structurally published. Visibility is not required for panel existence.
        """
        control = None
        panel = None

        candidates = [
            page.get_by_role("tab", name=label, exact=True),
            page.locator(f"[role='tab']:has-text('{label}')"),
            page.get_by_text(label, exact=True),
        ]

        for locator in candidates:
            for i in range(locator.count()):
                item = locator.nth(i)
                try:
                    if item.get_attribute("role") == "tab" and item.is_visible():
                        control = item
                        break
                except Exception:
                    continue
            if control is not None:
                break

        # Preferred ARIA relationship.
        if control is not None:
            try:
                panel_id = control.get_attribute("aria-controls")
            except Exception:
                panel_id = None

            if panel_id:
                candidate = page.locator(f"#{panel_id}")
                if candidate.count() > 0:
                    panel = candidate.first

        # Structural fallback: find any tabpanel containing the exact heading,
        # even when the panel is hidden.
        if panel is None:
            panels = page.locator("[role='tabpanel']")
            for i in range(panels.count()):
                candidate = panels.nth(i)
                try:
                    headings = candidate.get_by_text(label, exact=True)
                    if headings.count() > 0:
                        panel = candidate
                        break
                except Exception:
                    continue

        return control, panel

    def _extract_items(self, panel, tab_label: str) -> List[str]:
        """
        Conservative extraction. This deliberately does not treat the heading
        itself or generic container text as equipment.
        """
        selectors = ["li", "[role='listitem']", "p", "span", "div"]

        ignored_exact = {
            "",
            self.STANDARD_TAB,
            self.OPTIONAL_TAB,
            "Műszaki adatok",
            "Autó leírása",
            "Havidíjban foglalt szolgáltatások",
        }

        ignored_contains = (
            "havidíjban foglalt szolgáltatások",
            "ajánlatkérés",
            "futamidő",
            "futásteljesítmény",
            "induló befizetés",
            "ft / hó",
            "ft/hó",
        )

        for selector in selectors:
            locator = panel.locator(selector)
            values = []
            seen = set()

            for i in range(locator.count()):
                node = locator.nth(i)

                try:
                    raw = node.inner_text().strip()
                except Exception:
                    continue

                text = " ".join(raw.split())

                if text in ignored_exact or not text:
                    continue
                if len(text) < 3 or len(text) > 220:
                    continue

                lowered = text.lower()
                if any(noise in lowered for noise in ignored_contains):
                    continue

                if selector in {"p", "span", "div"}:
                    try:
                        if node.locator(":scope > *").count() > 0:
                            continue
                    except Exception:
                        pass

                if text in seen:
                    continue

                seen.add(text)
                values.append(text)

            if values:
                return values

        return []
