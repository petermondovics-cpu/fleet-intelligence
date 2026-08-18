# Fleet Intelligence — Current Project State

## Current checkpoint

Git branch:

    feature/domain-v2

Known checkpoint commit:

    5580fad
    checkpoint: comparison v2 benchmark dashboard v3 contract resolver v3

Python environment:

    .venv312
    Python 3.12

This document includes the current uncommitted validation state as of
2026-08-18.

---

## Current system capabilities

The repository currently contains a working evidence-first comparison pipeline including:

- market offer inventory
- comparable vehicle grouping
- market pair generation
- live provider acquisition
- Arval exact-offer acquisition
- Ayvens offer acquisition
- vehicle identity normalization
- variant equivalence assessment
- equipment evidence/value assessment
- service semantic comparison
- financial evidence provenance
- explicit contract-state evidence
- full comparison orchestration
- decision explanation
- comparison.v2 API presentation
- benchmark execution/persistence
- decision-aware benchmark dashboard
- evidence-plan dashboard

comparison.v2 provides one unified response containing:

- comparison status
- price_comparison_allowed
- price_winner
- offer information
- dimension statuses
- blockers
- decision verdict
- decision reasons
- observed nominal price difference
- confidence
- management summary
- next best action

comparison.v1 can still be projected explicitly.

---

## Current benchmark baseline

The most recent Contract V3 full-market benchmark before the bounded-retry
experiment was:

    run_id: 9
    status: PARTIAL
    candidate_count: 5
    evaluated_count: 2
    failed_count: 3
    price_comparable_count: 0

Both successfully evaluated Opel Combo pairs returned:

    INSUFFICIENT_EVIDENCE

Both evaluated pairs currently contain:

    NO_COMMON_PRICED_CONTRACT_STATE
    DOWN_PAYMENT_EVIDENCE_INCOMPLETE
    SERVICE_PARTIAL_EQUIVALENCE
    VEHICLE_VARIANT_DIFFERENCE

The three failed pairs were live navigation failures:

    BYD ATTO 2:
        Arval Page.goto timeout

    BYD SEAL U:
        Ayvens Page.goto timeout

    BYD SEALION 7:
        Ayvens Page.goto timeout

All three BYD groups passed separate targeted headed bridge runs in the same
development session. The run 9 failures are therefore classified as transient
provider/network load failures, not deterministic contract regressions.

A bounded one-retry navigation experiment was then tested in run 10:

    status: FAILED
    candidate_count: 5
    evaluated_count: 0
    failed_count: 5
    price_comparable_count: 0

Failures occurred across initial offer loading, manufacturer acquisition and
Ayvens trim/API acquisition. The retry did not improve batch reliability and
was fully reverted. Run 10 is retained as diagnostic evidence that blind
per-navigation retry is not a root-cause fix and may add provider load.

Run 10 also exposed a separate isolation defect: an exception from optional
BYD manufacturer equipment discovery could escape the acquisition layer and
abort the whole pair as BRIDGE_EXCEPTION. Manufacturer discovery exceptions
are now converted to explicit UNRESOLVED manufacturer equipment evidence.
Provider evidence remains unchanged and the comparison continues with its
equipment blocker intact.

A normal headed ATTO 2 bridge run (including manufacturer acquisition) passed
after this change:

    bridge_status: EVALUATED
    comparison_status: INSUFFICIENT_EVIDENCE
    price_comparison_allowed: False
    price_winner: None

The system is intentionally refusing to rank prices while these blockers remain.

---

## Current benchmark pairs

Current market benchmark includes:

    BYD::ATTO 2::PHEV
    BYD::SEAL U::PHEV
    BYD::SEALION 7::EV
    OPEL::COMBO::DIESEL
    OPEL::COMBO::DIESEL

There are 5 offer pairs across 4 unique vehicle groups.

---

## Contract Normalization V3

ContractNormalizationEvidenceResolverV3 has been integrated into:

    MarketPairFullComparisonBridge

The integration is live and operational.

A dedicated live integration test passed with:

    contract_method:
        EXPLICIT_COMMON_CONTRACT_STATE

The resolver attempts explicit common coordinates such as:

    60 months / 20,000 km/year
    48 months / 20,000 km/year
    36 months / 20,000 km/year

It resolves only if both providers have an explicit price for the same coordinate.

No interpolation, extrapolation or provider term factor is allowed.

---

## Current Contract V3 evidence

### BYD ATTO 2 PHEV

Observed:

    Arval:
        60m / 20,000 km = 192,312 HUF

    Ayvens:
        48m / 20,000 km = 189,990 HUF

Attempted:

    60m / 20,000 km
    48m / 20,000 km
    36m / 20,000 km

The current advertised Ayvens observation is now retained by the live bridge.
No explicit common priced coordinate was found.

---

### BYD SEAL U PHEV

Observed:

    Arval:
        60m / 20,000 km = 218,430 HUF

    Ayvens:
        48m / 20,000 km = 245,990 HUF

The current advertised Ayvens observation is now retained by the live bridge.
No explicit common priced coordinate was found.

---

### BYD SEALION 7 EV

Observed:

    Arval:
        60m / 20,000 km = 285,600 HUF

    Ayvens:
        48m / 20,000 km = 251,990 HUF

The full-market run timed out while loading Ayvens, but a subsequent targeted
headed bridge retry completed successfully and retained this current state.
No explicit common priced coordinate was found.

---

### Opel Combo Diesel — evaluated pair

Observed:

    Arval:
        60m / 20,000 km = 135,782 HUF

    Ayvens:
        48m / 20,000 km = 140,990 HUF

No explicit common priced coordinate was found.

---

### Opel Combo Diesel — second evaluated pair

Observed:

    Arval:
        60m / 20,000 km = 144,490 HUF

    Ayvens:
        48m / 20,000 km = 140,990 HUF

The former Ayvens trim/version load failure did not recur in run 9. The strict
exact-offer API `configuration` fallback is available when the DOM trim is
missing. No explicit common priced coordinate was found.

---

## Important current observation

The Ayvens current-state propagation root cause was identified and fixed.

Contract V3 previously rediscovered each provider's current coordinate even
though that exact advertised offer had already been recorded as
CURRENT_EXACT_OFFER. A different financial UI state at the same coordinate
could therefore create a price conflict and remove the whole coordinate during
deduplication.

Discovery now targets alternative coordinates only. The current exact-offer
observation remains authoritative, while contradictory evidence at genuine
alternative coordinates is still rejected.

The MarketPair bridge also skips the legacy CONTRACT acquisition task because
its candidates were not consumed by EvidenceEnrichmentBridge and the
authoritative V3 resolver runs immediately afterward. Other router callers keep
the previous behavior by default.

Ayvens trim parsing now has a strict exact-offer provider API fallback. Only a
non-empty explicit `data.configuration` value is accepted; model/capability
metadata remains insufficient.

---

## Ayvens contract evidence architecture

Current Ayvens contract evidence uses an exact-priced-contract resolver with provider API/UI acquisition.

The resolver is intentionally conservative.

A duration/mileage option without an explicit associated price is not price evidence.

If provider API data stores contract coordinates and prices in different structures, investigate the schema before changing matching behavior.

Do not join unrelated JSON values merely because they appear in the same payload.

Any schema-specific relationship used for price evidence must itself be explicit and defensible.

---

## Current development priority

The Ayvens current-state propagation patch is now validated across all four
unique vehicle groups. Both Opel Combo offer pairs were also evaluated in the
full-market run.

Targeted headed live bridge tests currently pass for:

    BYD::ATTO 2::PHEV
    BYD::SEAL U::PHEV
    BYD::SEALION 7::EV
    OPEL::COMBO::DIESEL

All three retained the current advertised Ayvens state and correctly remained
EVIDENCE_UNRESOLVED because no explicit common priced coordinate was found.

The next priorities are to diagnose batch-level live-load behavior (provider
request pacing and throttling) without weakening evidence rules, and separately
triage historical test debt. Browser lifecycle has been checked: each pair
already receives a fresh Playwright/browser lifecycle. Optional manufacturer
failure is now isolated from core comparison completion.

Structured in-memory bridge stage timings are now available and propagated to
BenchmarkPairExecution without changing the persisted benchmark schema or any
decision/blocker text. A live ATTO 2 diagnostic measured:

    load_left (Arval): 12.393 seconds
    load_right (Ayvens): 61.290 seconds -> Page.goto timeout

The matching Ayvens exact-offer API remained healthy and returned explicit
configuration metadata in 4.7 seconds. Commit-only navigation was confirmed
unsafe because HTTP 200 can arrive before any offer DOM exists.

Ayvens loading now navigates to HTTP commit and then waits specifically for the
explicit advertised monthly-fee DOM element. This is only a readiness signal;
the evidence-aware builder still independently validates identity, fee,
duration and mileage. Missing priced-offer DOM remains LOAD_FAILED.

A normal headed ATTO 2 bridge run then completed with:

    load_left (Arval): 6.593 seconds
    load_right (Ayvens): 25.413 seconds
    acquisition: 209.608 seconds
    contract_evidence: 42.369 seconds
    bridge_status: EVALUATED
    comparison_status: INSUFFICIENT_EVIDENCE
    price_winner: None

The current live bottleneck has therefore moved from initial Ayvens loading to
the broad acquisition stage. Down-payment evidence was unavailable in this run
and correctly remained UNKNOWN with DOWN_PAYMENT_EVIDENCE_INCOMPLETE.

The historical deterministic script inventory currently reports 97 passing
and 19 failing scripts. The failures include obsolete API/source-inspection
expectations and two scripts that launch Chromium despite not being named as
live tests. These should be triaged separately; none failed on the modified
Ayvens current-state, identity fallback, or router-filter regression paths.

---

## Known good behavior

The following behavior is intentional and must remain:

If:

    Arval = 60m / 20,000 km
    Ayvens = 48m / 20,000 km

and no explicit common priced state exists, then:

    contract_status = EVIDENCE_UNRESOLVED
    contract_confidence = 0
    price_comparison_allowed = False

The provider with the lower nominal advertised monthly fee must NOT automatically become price_winner.

---

## Definition of success for the next development phase

Success does NOT mean forcing price_comparable_count above zero.

Success means:

- all available explicit provider evidence is reliably captured
- current advertised states are not accidentally lost
- alternative states are accepted only with explicit price evidence
- missing evidence remains missing
- benchmark runs are reproducible
- deterministic regressions are covered by tests
- live-provider failures are diagnosed separately from comparison logic
- price ranking occurs only when all required evidence supports it

A benchmark that still returns INSUFFICIENT_EVIDENCE may be completely correct.
