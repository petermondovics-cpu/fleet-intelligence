from pathlib import Path

PATH = Path(
    "market_intelligence/market_pair_full_comparison_bridge.py"
)
BACKUP = Path(
    "market_intelligence/"
    "market_pair_full_comparison_bridge.py.pre_arval_route_aware_load_v1.bak"
)

IMPORT_ANCHOR = """from scrapers.arval.evidence_aware_builder import (
    ArvalEvidenceAwareBuilder,
)
"""

IMPORT_NEW = IMPORT_ANCHOR + """from scrapers.arval.offer_route_resolver import (
    ROUTE_LIVE,
    ArvalOfferRouteResolver,
)
"""

LOAD_OLD = """    @classmethod
    def _load(
        cls,
        browser,
        provider: str,
        url: str,
    ):
        builder = cls._builder_for(
            provider
        )
        page = browser.new_page()

        try:
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(1800)
            cls._dismiss(page)
            return builder.build(page)
        finally:
            page.close()
"""

LOAD_NEW = """    @classmethod
    def _load(
        cls,
        browser,
        provider: str,
        url: str,
    ):
        builder = cls._builder_for(
            provider
        )
        page = browser.new_page()

        try:
            provider_key = (
                provider
                .strip()
                .casefold()
            )

            if provider_key == "arval":
                route = (
                    ArvalOfferRouteResolver()
                    .resolve(
                        page,
                        url,
                        timeout=60000,
                        settle_ms=1500,
                    )
                )

                if (
                    route.status
                    != ROUTE_LIVE
                    or not route.resolved_url
                ):
                    raise ValueError(
                        "Arval exact-offer route could not be "
                        "validated before builder execution. "
                        + route.diagnostic
                    )

                # Route resolver has already navigated the page to the
                # validated exact-offer route. Do not navigate again.
                cls._dismiss(page)
                page.wait_for_timeout(300)
                return builder.build(page)

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(1800)
            cls._dismiss(page)
            return builder.build(page)

        finally:
            page.close()
"""


def main():
    if not PATH.exists():
        raise SystemExit(
            f"Missing: {PATH}"
        )

    text = PATH.read_text(
        encoding="utf-8"
    )

    if (
        "ArvalOfferRouteResolver" in text
        and "Arval exact-offer route could not be" in text
    ):
        print(
            "Already patched - no changes made."
        )
        return

    if IMPORT_ANCHOR not in text:
        raise SystemExit(
            "Arval builder import anchor not found; "
            "refusing unsafe patch."
        )

    if LOAD_OLD not in text:
        raise SystemExit(
            "_load() anchor not found; refusing unsafe patch."
        )

    if not BACKUP.exists():
        BACKUP.write_text(
            text,
            encoding="utf-8",
        )
        print(
            "Backup:",
            BACKUP,
        )

    text = text.replace(
        IMPORT_ANCHOR,
        IMPORT_NEW,
        1,
    )

    text = text.replace(
        LOAD_OLD,
        LOAD_NEW,
        1,
    )

    compile(
        text,
        str(PATH),
        "exec",
    )

    PATH.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Patched:",
        PATH,
    )
    print(
        "Arval route-aware bridge load V1: INSTALLED"
    )


if __name__ == "__main__":
    main()
