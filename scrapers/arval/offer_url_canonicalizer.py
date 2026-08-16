from dataclasses import dataclass
from urllib.parse import (
    urlsplit,
    urlunsplit,
)


ARVAL_HOSTS = {
    "arval.hu",
    "www.arval.hu",
}

OFFER_MARKER = (
    "tartos-berleti-ajantlat"
)


@dataclass(frozen=True)
class ArvalUrlCanonicalizationResult:
    original_url: str
    canonical_url: str
    changed: bool
    reason: str


class ArvalOfferUrlCanonicalizer:
    """
    Arval Offer URL Canonicalizer V1.

    Scope
    -----
    Repairs only one safely identifiable URL defect:

        .../tartos-berleti-ajandlat/<slug>/<slug>

    becomes:

        .../tartos-berleti-ajandlat/<slug>

    Safety
    ------
    - only Arval hosts are touched;
    - only paths containing the exact offer marker are touched;
    - only adjacent IDENTICAL final path segments are collapsed;
    - distinct final segments are preserved;
    - query string and fragment are preserved;
    - no vehicle identity is inferred from the URL;
    - no redirect behavior is guessed.
    """

    def canonicalize(
        self,
        url: str,
    ) -> ArvalUrlCanonicalizationResult:

        if not url:
            return ArvalUrlCanonicalizationResult(
                original_url=url,
                canonical_url=url,
                changed=False,
                reason="EMPTY_URL",
            )

        try:
            parts = urlsplit(
                url
            )
        except Exception:
            return ArvalUrlCanonicalizationResult(
                original_url=url,
                canonical_url=url,
                changed=False,
                reason="URL_PARSE_FAILED",
            )

        host = (
            parts.hostname
            or ""
        ).casefold()

        if host not in ARVAL_HOSTS:
            return ArvalUrlCanonicalizationResult(
                original_url=url,
                canonical_url=url,
                changed=False,
                reason="NON_ARVAL_HOST",
            )

        segments = [
            segment
            for segment in parts.path.split("/")
            if segment
        ]

        if OFFER_MARKER not in segments:
            return ArvalUrlCanonicalizationResult(
                original_url=url,
                canonical_url=url,
                changed=False,
                reason="NON_OFFER_PATH",
            )

        if len(
            segments
        ) < 2:
            return ArvalUrlCanonicalizationResult(
                original_url=url,
                canonical_url=url,
                changed=False,
                reason="NO_DUPLICATE_FINAL_SEGMENTS",
            )

        left = segments[-2]
        right = segments[-1]

        if (
            left.casefold()
            != right.casefold()
        ):
            return ArvalUrlCanonicalizationResult(
                original_url=url,
                canonical_url=url,
                changed=False,
                reason="FINAL_SEGMENTS_DIFFER",
            )

        canonical_segments = (
            segments[:-1]
        )

        canonical_path = (
            "/"
            + "/".join(
                canonical_segments
            )
        )

        canonical = urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                canonical_path,
                parts.query,
                parts.fragment,
            )
        )

        return ArvalUrlCanonicalizationResult(
            original_url=url,
            canonical_url=canonical,
            changed=True,
            reason=(
                "DUPLICATED_FINAL_OFFER_SLUG_COLLAPSED"
            ),
        )

    def canonical_url(
        self,
        url: str,
    ) -> str:
        return (
            self.canonicalize(
                url
            )
            .canonical_url
        )
