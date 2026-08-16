from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class EquipmentValueRule:
    """
    Canonical equipment valuation rule.

    score:
        Abstract comparison points only.
        These scores are NOT HUF values and must never be added to prices.
    """

    canonical_name: str
    aliases: Tuple[str, ...]
    category: str
    score: int


@dataclass(frozen=True)
class EquipmentValueResult:
    known_score: int
    unknown_items: Tuple[str, ...]
    matched_items: Tuple[str, ...]

    @property
    def fully_scored(self) -> bool:
        return len(self.unknown_items) == 0


@dataclass(frozen=True)
class EquipmentValueComparison:
    left: EquipmentValueResult
    right: EquipmentValueResult
    score_delta: int

    @property
    def fully_scored(self) -> bool:
        return (
            self.left.fully_scored
            and self.right.fully_scored
        )


class EquipmentValueNormalizer:
    """
    Equipment Value Normalization V3.

    Goals:
    - preserve evidence-first behavior;
    - accept both EquipmentItem-like objects and validated acquisition strings;
    - support one source item mapping to multiple canonical equipment features;
    - deduplicate canonical features across source items;
    - never silently value an unknown source item as zero.

    Safety model
    ------------
    Simple items:
        Must exactly match a configured alias.

    Known compound manufacturer items:
        Must exactly match a configured compound source phrase.
        That phrase may expand into multiple canonical features.

    Unknown / partially unsupported wording:
        Remains in unknown_items and blocks fully_scored=True.

    This deliberately avoids fuzzy matching and broad substring inference.
    """

    RULES = (
        EquipmentValueRule(
            canonical_name="ADAPTIVE_CRUISE_CONTROL",
            aliases=(
                "adaptív tempomat",
                "adaptív sebességtartó",
                "adaptív sebességtartó stop&go rendszerrel",
            ),
            category="ADAS",
            score=5,
        ),
        EquipmentValueRule(
            canonical_name="LED_HEADLIGHTS",
            aliases=(
                "led fényszóró",
                "adaptív led fényszórók",
            ),
            category="LIGHTING",
            score=3,
        ),
        EquipmentValueRule(
            canonical_name="HEATED_STEERING_WHEEL",
            aliases=(
                "fűthető kormánykerék",
            ),
            category="COMFORT",
            score=2,
        ),
        EquipmentValueRule(
            canonical_name="REAR_CAMERA",
            aliases=(
                "tolatókamera",
                "180 fokos tolatókamera",
            ),
            category="PARKING",
            score=3,
        ),
        EquipmentValueRule(
            canonical_name="KEYLESS_ENTRY_START",
            aliases=(
                "kulcs nélküli nyitás és indítás",
                "kulcs nélküli indítás",
            ),
            category="COMFORT",
            score=2,
        ),
        EquipmentValueRule(
            canonical_name="METALLIC_PAINT",
            aliases=(
                "metálfényezés",
                "kristall ezüst metálfényezés",
            ),
            category="EXTERIOR",
            score=2,
        ),
        EquipmentValueRule(
            canonical_name="HEATED_MIRRORS",
            aliases=(
                "elektromosan állítható, fűthető külső tükrök",
            ),
            category="COMFORT",
            score=1,
        ),
        EquipmentValueRule(
            canonical_name="PARKING_SENSORS_FRONT_REAR",
            aliases=(
                "parkolóradar elöl és hátul",
            ),
            category="PARKING",
            score=2,
        ),
        EquipmentValueRule(
            canonical_name="WIRELESS_PHONE_PROJECTION",
            aliases=(
                "vezeték nélküli apple carplay és android auto telefonkivetítés",
            ),
            category="INFOTAINMENT",
            score=2,
        ),
        EquipmentValueRule(
            canonical_name="AUTOMATIC_CLIMATE_CONTROL",
            aliases=(
                "automata légkondicionáló",
            ),
            category="COMFORT",
            score=2,
        ),

        # ----------------------------------------------------
        # BYD / manufacturer canonical features
        # ----------------------------------------------------

        EquipmentValueRule(
            canonical_name="CLOTH_INTERIOR",
            aliases=(),
            category="INTERIOR",
            score=1,
        ),
        EquipmentValueRule(
            canonical_name="REAR_PARKING_SENSORS",
            aliases=(),
            category="PARKING",
            score=1,
        ),
        EquipmentValueRule(
            canonical_name="RAIN_SENSING_WIPERS",
            aliases=(),
            category="COMFORT",
            score=1,
        ),
        EquipmentValueRule(
            canonical_name="INFOTAINMENT_TOUCHSCREEN",
            aliases=(),
            category="INFOTAINMENT",
            score=2,
        ),
        EquipmentValueRule(
            canonical_name="DIGITAL_DRIVER_DISPLAY",
            aliases=(),
            category="INFOTAINMENT",
            score=1,
        ),
        EquipmentValueRule(
            canonical_name="GOOGLE_AUTOMOTIVE_SERVICES",
            aliases=(),
            category="INFOTAINMENT",
            score=2,
        ),
        EquipmentValueRule(
            canonical_name="APPLE_CARPLAY",
            aliases=(),
            category="INFOTAINMENT",
            score=1,
        ),
        EquipmentValueRule(
            canonical_name="ANDROID_AUTO",
            aliases=(),
            category="INFOTAINMENT",
            score=1,
        ),
        EquipmentValueRule(
            canonical_name="VEGAN_LEATHER_INTERIOR",
            aliases=(),
            category="INTERIOR",
            score=2,
        ),
        EquipmentValueRule(
            canonical_name="PANORAMIC_ROOF",
            aliases=(),
            category="COMFORT",
            score=4,
        ),
        EquipmentValueRule(
            canonical_name="ELECTRIC_SUNSHADE",
            aliases=(),
            category="COMFORT",
            score=1,
        ),
        EquipmentValueRule(
            canonical_name="SURROUND_VIEW_CAMERA",
            aliases=(),
            category="PARKING",
            score=4,
        ),
        EquipmentValueRule(
            canonical_name="FRONT_PARKING_SENSORS",
            aliases=(),
            category="PARKING",
            score=1,
        ),
        EquipmentValueRule(
            canonical_name="HEATED_FRONT_SEATS",
            aliases=(),
            category="COMFORT",
            score=3,
        ),
        EquipmentValueRule(
            canonical_name="WIRELESS_PHONE_CHARGING",
            aliases=(),
            category="INFOTAINMENT",
            score=2,
        ),
        EquipmentValueRule(
            canonical_name="ROOF_RAILS",
            aliases=(),
            category="EXTERIOR",
            score=1,
        ),
        EquipmentValueRule(
            canonical_name="REAR_PRIVACY_GLASS",
            aliases=(),
            category="EXTERIOR",
            score=1,
        ),
    )

    # Exact known manufacturer source phrases.
    #
    # One phrase may expand into multiple canonical features.
    # Exact matching is intentional: if manufacturer wording changes,
    # the new wording becomes UNKNOWN until explicitly reviewed.
    COMPOUND_ITEMS = {
        "premium active black cloth interior": (
            "CLOTH_INTERIOR",
        ),
        "reversing camera with rear parking sensors": (
            "REAR_CAMERA",
            "REAR_PARKING_SENSORS",
        ),
        "automatic led headlights & rain-sensing front wipers": (
            "LED_HEADLIGHTS",
            "RAIN_SENSING_WIPERS",
        ),
        "12.8” infotainment touchscreen & 8.8” driver’s display": (
            "INFOTAINMENT_TOUCHSCREEN",
            "DIGITAL_DRIVER_DISPLAY",
        ),
        "google automotive services (gas) built-in": (
            "GOOGLE_AUTOMOTIVE_SERVICES",
        ),
        "android auto & apple carplay as standard": (
            "ANDROID_AUTO",
            "APPLE_CARPLAY",
        ),
        "high-quality vegan leather interior": (
            "VEGAN_LEATHER_INTERIOR",
        ),
        "panoramic roof with electric sunshade": (
            "PANORAMIC_ROOF",
            "ELECTRIC_SUNSHADE",
        ),
        "360◦ camera with front & rear parking sensors": (
            "SURROUND_VIEW_CAMERA",
            "FRONT_PARKING_SENSORS",
            "REAR_PARKING_SENSORS",
        ),
        "360° camera with front & rear parking sensors": (
            "SURROUND_VIEW_CAMERA",
            "FRONT_PARKING_SENSORS",
            "REAR_PARKING_SENSORS",
        ),
        "heated front seats & heated steering wheel": (
            "HEATED_FRONT_SEATS",
            "HEATED_STEERING_WHEEL",
        ),
        "smartphone wireless charging": (
            "WIRELESS_PHONE_CHARGING",
        ),
        "aluminium roof rail & rear privacy glass": (
            "ROOF_RAILS",
            "REAR_PRIVACY_GLASS",
        ),
    }

    def __init__(self):

        self._alias_map: Dict[
            str,
            EquipmentValueRule,
        ] = {}

        self._rule_by_name: Dict[
            str,
            EquipmentValueRule,
        ] = {
            rule.canonical_name: rule
            for rule in self.RULES
        }

        for rule in self.RULES:
            for alias in rule.aliases:
                self._alias_map[
                    self._normalize(alias)
                ] = rule

        self._compound_map = {
            self._normalize(source): tuple(features)
            for source, features in self.COMPOUND_ITEMS.items()
        }

        # Fail early if a compound profile refers to a missing rule.
        for features in self._compound_map.values():
            for canonical_name in features:
                if canonical_name not in self._rule_by_name:
                    raise ValueError(
                        "Compound equipment profile refers to "
                        f"undefined canonical rule: {canonical_name}"
                    )

    def score_items(
        self,
        items,
    ) -> EquipmentValueResult:

        score = 0
        unknown: List[str] = []
        matched: List[str] = []

        seen_canonical = set()

        for item in items:

            normalized_item = (
                self._coerce_item(item)
            )

            if normalized_item is None:
                continue

            name, included = normalized_item

            if included is not True:
                continue

            key = self._normalize(
                name
            )

            canonical_names = (
                self._canonical_names_for_key(
                    key
                )
            )

            if not canonical_names:
                unknown.append(
                    name
                )
                continue

            for canonical_name in canonical_names:

                if canonical_name in seen_canonical:
                    continue

                rule = self._rule_by_name[
                    canonical_name
                ]

                seen_canonical.add(
                    canonical_name
                )

                score += rule.score

                matched.append(
                    canonical_name
                )

        return EquipmentValueResult(
            known_score=score,
            unknown_items=tuple(unknown),
            matched_items=tuple(matched),
        )

    def compare(
        self,
        left_items,
        right_items,
    ) -> EquipmentValueComparison:

        left = self.score_items(
            left_items
        )

        right = self.score_items(
            right_items
        )

        return EquipmentValueComparison(
            left=left,
            right=right,
            score_delta=(
                right.known_score
                - left.known_score
            ),
        )

    def _canonical_names_for_key(
        self,
        key: str,
    ) -> Tuple[str, ...]:

        compound = self._compound_map.get(
            key
        )

        if compound is not None:
            return compound

        simple = self._alias_map.get(
            key
        )

        if simple is not None:
            return (
                simple.canonical_name,
            )

        return ()

    @staticmethod
    def _coerce_item(
        item,
    ):
        """
        Normalize supported equipment input shapes.

        EquipmentItem-like:
            object with .name and .included

        Validated acquisition/manufacturer evidence:
            non-empty string -> included=True

        Unsupported shapes are ignored rather than guessed.
        """

        if isinstance(item, str):
            name = item.strip()

            if not name:
                return None

            return (
                name,
                True,
            )

        name = getattr(
            item,
            "name",
            None,
        )

        included = getattr(
            item,
            "included",
            None,
        )

        if (
            not isinstance(name, str)
            or not name.strip()
        ):
            return None

        return (
            name.strip(),
            included,
        )

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:

        return " ".join(
            text.casefold()
            .replace("–", "-")
            .strip()
            .split()
        )
