from dataclasses import dataclass
from typing import Dict, Optional, Tuple

SERVICE_TRUE = "TRUE"
SERVICE_FALSE = "FALSE"
SERVICE_UNRESOLVED = "UNRESOLVED"

@dataclass(frozen=True)
class ServiceEvidenceResolution:
    provider: str
    canonical_code: str
    status: str
    included: Optional[bool]
    applicability_scope: str
    source_type: Optional[str]
    source_url: Optional[str]
    source_text: Optional[str]
    diagnostic: str

class OneSidedServiceEvidenceResolver:
    ALLOWED_SCOPES = {"EXACT_OFFER","ALL_OFFERS_IN_PROGRAM","UNIVERSAL_PROVIDER_TERMS"}
    TARGETS = {
        "Ayvens": {
            "CLAIMS_MANAGEMENT": ("káresemény-kezelés","kárrendezés","kárügyintézés","káresemény"),
            "FINANCING": ("finanszírozás","finanszírozási"),
        },
        "Arval": {
            "TAXES": ("vonatkozó adók","adók","adókat","adóterhek"),
        },
    }
    POSITIVE_MARKERS = ("tartalmazza","tartalmaz","magában foglalja","magában foglal","havidíjban foglalt","included")
    NEGATIVE_MARKERS = ("nem tartalmazza","nem tartalmaz","nem foglalja magában","nem része","külön díj ellenében","külön fizetendő","excluded","not included")
    UNIVERSAL_MARKERS = ("minden tartós bérleti szerződés","minden tartós bérleti ajánlat","minden ügyfelünk számára","minden bérleti konstrukció","a havidíj minden esetben tartalmazza","minden ajánlatunk tartalmazza")

    def resolve_candidate(self, *, provider, canonical_code, source_type, source_url, source_text, applicability_scope):
        aliases = self.TARGETS.get(provider, {}).get(canonical_code)
        if not aliases:
            return self._u(provider, canonical_code, applicability_scope, source_type, source_url, source_text, "No targeted resolver rule exists.")

        text = " ".join((source_text or "").split())
        lowered = text.casefold()

        if not any(a.casefold() in lowered for a in aliases):
            return self._u(provider, canonical_code, applicability_scope, source_type, source_url, source_text, "Target wording not observed.")

        scope = applicability_scope
        if scope == "GENERIC_PROVIDER_DOCUMENTATION":
            if any(m in lowered for m in self.UNIVERSAL_MARKERS):
                scope = "UNIVERSAL_PROVIDER_TERMS"
            else:
                return self._u(provider, canonical_code, scope, source_type, source_url, source_text, "Generic documentation does not prove universal applicability.")

        if scope not in self.ALLOWED_SCOPES:
            return self._u(provider, canonical_code, scope, source_type, source_url, source_text, "Applicability scope too weak.")

        if self._near(lowered, aliases, self.NEGATIVE_MARKERS):
            return ServiceEvidenceResolution(provider, canonical_code, SERVICE_FALSE, False, scope, source_type, source_url, source_text, "Explicit exclusion wording found.")

        if self._near(lowered, aliases, self.POSITIVE_MARKERS):
            return ServiceEvidenceResolution(provider, canonical_code, SERVICE_TRUE, True, scope, source_type, source_url, source_text, "Explicit inclusion wording found.")

        return self._u(provider, canonical_code, scope, source_type, source_url, source_text, "Service mentioned without explicit inclusion/exclusion.")

    def resolve_gaps(self, *, arval_sources: Tuple[Dict, ...], ayvens_sources: Tuple[Dict, ...]):
        tasks = (
            ("Ayvens","CLAIMS_MANAGEMENT",ayvens_sources),
            ("Ayvens","FINANCING",ayvens_sources),
            ("Arval","TAXES",arval_sources),
        )
        out = []
        for provider, code, sources in tasks:
            best = None
            for s in sources:
                r = self.resolve_candidate(
                    provider=provider,
                    canonical_code=code,
                    source_type=s.get("source_type"),
                    source_url=s.get("source_url"),
                    source_text=s.get("source_text") or "",
                    applicability_scope=s.get("applicability_scope","UNKNOWN"),
                )
                if r.status in {SERVICE_TRUE,SERVICE_FALSE}:
                    best = r
                    break
                if best is None:
                    best = r
            if best is None:
                best = self._u(provider, code, "UNKNOWN", None, None, None, "No source candidate supplied.")
            out.append(best)
        return tuple(out)

    @staticmethod
    def _near(lowered, aliases, markers, window=220):
        for alias in aliases:
            needle = alias.casefold()
            start = 0
            while True:
                idx = lowered.find(needle, start)
                if idx < 0:
                    break
                ctx = lowered[max(0,idx-window):min(len(lowered),idx+len(needle)+window)]
                if any(m in ctx for m in markers):
                    return True
                start = idx + len(needle)
        return False

    @staticmethod
    def _u(provider, code, scope, source_type, source_url, source_text, diagnostic):
        return ServiceEvidenceResolution(provider, code, SERVICE_UNRESOLVED, None, scope, source_type, source_url, source_text, diagnostic)
