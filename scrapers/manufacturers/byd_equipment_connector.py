import re


class BYDManufacturerEquipmentConnector:
    """
    BYD Manufacturer Equipment Connector V2.

    Official-source-only connector for exact BYD derivative equipment
    discovery.

    Current supported family:
        BYD ATTO 2 DM-i

    Official sources:
    - BYD Hungary model page
    - BYD Europe / BYD media technical specification
    - BYD official configurator where version differentiation is explicit

    Safety:
    - source domain must belong to BYD;
    - exact model family must be ATTO 2 DM-i / canonical ATTO 2 PHEV;
    - Active and Boost are never silently collapsed;
    - generic model-level equipment is not promoted to exact trim equipment
      unless the source explicitly marks it as common/standard;
    - "some versions" wording is not assigned to a trim unless version is
      explicitly identified.
    """

    MODEL_URL = (
        "https://www.byd.com/hu/hibrid-autok/atto-2-dm-i"
    )

    MEDIA_URL = (
        "https://media.byd.com/"
        "its-not-a-car-its-a-byd-super-hybrid-atto-2-dm-i-"
        "arrives-to-redefine-the-compact-suv/?lang=eng"
    )

    CONFIGURATOR_URL = (
        "https://www.byd.com/uk/configurator/atto-2-dm-i"
    )

    ALLOWED_HOST_MARKERS = (
        "byd.com",
        "media.byd.com",
    )

    def __init__(self, browser):
        self.browser = browser

    def discover(self, task, offer):
        target_variant = self._target_variant(
            offer.trim
        )

        if target_variant is None:
            return None

        # Prefer official source with explicit Active/Boost distinction.
        candidate = self._from_configurator(
            target_variant
        )

        if candidate is not None:
            return candidate

        candidate = self._from_media_spec(
            target_variant
        )

        if candidate is not None:
            return candidate

        # Model page can provide model-level common equipment, but V1
        # refuses to claim exact variant equivalence from it.
        return None

    # ========================================================
    # CONFIGURATOR
    # ========================================================

    def _from_configurator(self, target_variant):
        page = self.browser.new_page()

        try:
            page.goto(
                self.CONFIGURATOR_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(1500)
            self._dismiss(page)

            if not self._official(page.url):
                return None

            text = page.locator("body").inner_text()

            sections = self._parse_configurator_variants(
                text
            )

            items = sections.get(
                target_variant
            )

            if not items:
                return None

            return {
                "source_type": "MANUFACTURER_MODEL_PAGE",
                "source_url": page.url,
                "source_text": (
                    f"Official BYD configurator: "
                    f"ATTO 2 DM-i {target_variant}"
                ),
                "brand": "BYD",
                "model": "ATTO 2 DM-i",
                "trim": target_variant.title(),
                "fuel_type": "PHEV",
                "variant_match_status": "EXACT",
                "equipment": tuple(items),
                "different_model_year": False,
            }

        finally:
            page.close()

    @classmethod
    def _parse_configurator_variants(
        cls,
        text,
    ):
        """
        Parse explicit Active / Boost equipment lines from official BYD
        configurator text.

        Boost includes "Active Specification +" plus listed extras, so the
        returned Boost set includes Active features + Boost extras.
        """

        clean = "\n".join(
            line.strip()
            for line in text.splitlines()
            if line.strip()
        )

        active_block = cls._between(
            clean,
            "\nActive\n",
            "\nBoost\n",
        )

        boost_block = cls._between_first_of(
            clean,
            "\nBoost\n",
            (
                "\nPaint\n",
                "\nExterior\n",
                "\nInterior\n",
                "\nWheels\n",
                "\nBuild your BYD\n",
                "\nExplore exterior details\n",
                "\nExplore interior details\n",
            ),
        )

        active = cls._bullet_features(
            active_block
        )

        boost_extra = cls._bullet_features(
            boost_block
        )

        # Prevent price/range lines from becoming equipment.
        active = [
            x for x in active
            if not cls._non_equipment_line(x)
        ]

        boost_extra = [
            x for x in boost_extra
            if not cls._non_equipment_line(x)
        ]

        boost = list(active)

        for item in boost_extra:
            if item not in boost:
                boost.append(item)

        return {
            "ACTIVE": active,
            "BOOST": boost,
        }

    # ========================================================
    # MEDIA TECHNICAL SPEC
    # ========================================================

    def _from_media_spec(
        self,
        target_variant,
    ):
        page = self.browser.new_page()

        try:
            page.goto(
                self.MEDIA_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(1500)
            self._dismiss(page)

            if not self._official(page.url):
                return None

            text = page.locator("body").inner_text()

            if (
                "ATTO 2 DM-i technical specifications"
                not in text
            ):
                return None

            if (
                "Active"
                not in text
                or "Boost"
                not in text
            ):
                return None

            # Media page proves the two official variants exist but is not
            # guaranteed to expose a clean full equipment matrix through
            # DOM text. V1 only uses it if explicit trim-marked feature
            # rows can be safely extracted.
            items = self._parse_media_variant_features(
                text,
                target_variant,
            )

            if not items:
                return None

            return {
                "source_type": "MANUFACTURER_SPECIFICATION",
                "source_url": page.url,
                "source_text": (
                    f"Official BYD media technical specification: "
                    f"ATTO 2 DM-i {target_variant}"
                ),
                "brand": "BYD",
                "model": "ATTO 2 DM-i",
                "trim": target_variant.title(),
                "fuel_type": "PHEV",
                "variant_match_status": "EXACT",
                "equipment": tuple(items),
                "different_model_year": False,
            }

        finally:
            page.close()

    @staticmethod
    def _parse_media_variant_features(
        text,
        target_variant,
    ):
        # Conservative V1: only extract features from lines that explicitly
        # name the target variant. Do not infer from general prose.
        out = []

        for line in text.splitlines():
            stripped = " ".join(
                line.split()
            )

            if not stripped:
                continue

            if target_variant.casefold() not in stripped.casefold():
                continue

            if len(stripped) > 220:
                continue

            if any(
                token in stripped.casefold()
                for token in (
                    "technical specifications",
                    "price",
                    "range",
                    "battery",
                    "power",
                )
            ):
                continue

            out.append(stripped)

        return out

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _target_variant(trim):
        value = (trim or "").upper()

        if "BOOST" in value:
            return "BOOST"

        if "ACTIVE" in value:
            return "ACTIVE"

        return None

    @classmethod
    def _official(
        cls,
        url,
    ):
        lowered = url.casefold()

        return any(
            marker in lowered
            for marker in cls.ALLOWED_HOST_MARKERS
        )

    @staticmethod
    def _between(
        text,
        start_marker,
        end_marker,
    ):
        start = text.find(start_marker)

        if start < 0:
            return ""

        start += len(start_marker)

        end = text.find(
            end_marker,
            start,
        )

        if end < 0:
            return text[start:]

        return text[start:end]

    @staticmethod
    def _between_first_of(
        text,
        start_marker,
        end_markers,
    ):
        start = text.find(start_marker)

        if start < 0:
            return ""

        start += len(start_marker)

        ends = []

        for marker in end_markers:
            idx = text.find(
                marker,
                start,
            )

            if idx >= 0:
                ends.append(idx)

        if not ends:
            return text[start:]

        return text[start:min(ends)]

    @staticmethod
    def _after(
        text,
        marker,
    ):
        idx = text.find(marker)

        if idx < 0:
            return ""

        return text[
            idx + len(marker):
        ]

    @staticmethod
    def _bullet_features(
        block,
    ):
        items = []

        for raw in block.splitlines():
            line = raw.strip()

            if not line:
                continue

            # Browser innerText commonly strips bullet glyphs, so accept
            # concise feature-like lines as well.
            line = re.sub(
                r"^[•●\-]+\s*",
                "",
                line,
            )

            if len(line) < 4:
                continue

            if line.casefold().startswith(
                "active specification +"
            ):
                continue

            if line.startswith("£"):
                continue

            items.append(line)

        return items

    @staticmethod
    def _non_equipment_line(
        line,
    ):
        value = line.casefold()

        return (
            "miles combined range" in value
            or "km combined range" in value
            or value.startswith("£")
            or "build your byd" in value
            or "choose a version" in value
            or value in {
                "paint",
                "included",
                "exterior",
                "interior",
                "wheels",
                "explore exterior details",
                "explore interior details",
            }
            or value.startswith("explore ")
            or value.endswith(" included")
        )

    @staticmethod
    def _dismiss(page):
        for selector in (
            "#onetrust-reject-all-handler",
            "#onetrust-accept-btn-handler",
            "button:has-text('Accept All')",
            "button:has-text('Reject All')",
            "button:has-text('Összes elfogadása')",
            "button:has-text('Elfogadom')",
        ):
            loc = page.locator(selector)

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
