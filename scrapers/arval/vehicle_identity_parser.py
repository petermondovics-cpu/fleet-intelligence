from playwright.sync_api import Page


class ArvalVehicleIdentityParser:
    """
    Evidence-first identity parser for Arval offer pages.

    Uses only page title text / breadcrumbs / URL.
    """

    def parse_brand(
        self,
        page: Page,
        title: str,
    ) -> str:

        value = title.strip()

        if not value:
            raise ValueError(
                "Arval title cannot be empty."
            )

        return value.split()[0]

    def parse_model_name(
        self,
        page: Page,
        title: str,
    ) -> str:
        """
        Conservative model extraction from title.

        For V1, preserve the vehicle designation after brand but before
        obvious engine/derivative tokens when possible.
        """

        value = title.strip()
        parts = value.split()

        if len(parts) < 2:
            raise ValueError(
                "Arval model could not be resolved."
            )

        brand = parts[0]
        remainder = parts[1:]

        stop_tokens = {
            "1.0", "1.2", "1.3", "1.4", "1.5",
            "1.6", "2.0", "2.2", "PHEV", "EV",
            "Hybrid", "Dízel", "Benzin",
        }

        model_parts = []

        for token in remainder:
            if token in stop_tokens:
                break

            model_parts.append(token)

        if not model_parts:
            # preserve observed text rather than inventing
            return " ".join(remainder)

        return " ".join(model_parts)

    def parse_trim(
        self,
        page: Page,
        title: str,
        brand: str,
        model: str,
    ) -> str:

        value = title.strip()

        prefix = f"{brand} {model}".strip()

        if value.lower().startswith(
            prefix.lower()
        ):
            remainder = value[
                len(prefix):
            ].strip(" -–|")

            if remainder:
                return remainder

        return value
