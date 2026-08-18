# Next Task — Batch Live-Load Isolation and Test-Debt Triage

## Objective

Isolate why sequential full-market runs degrade across provider and
manufacturer navigation, then triage the historical deterministic test
failures without changing comparison or evidence semantics.

Do NOT attempt to increase price comparability by weakening comparison rules.

## Completed investigation

Previous baseline (run 8):

    candidate_count: 5
    evaluated_count: 4
    failed_count: 1
    price_comparable_count: 0

The four evaluated run 8 pairs contained:

    NO_COMMON_PRICED_CONTRACT_STATE

The loss of current Ayvens evidence was reproduced and fixed. Targeted live
bridge tests now retain:

    BYD ATTO 2 / Ayvens
    48 months / 20,000 km/year
    189,990 HUF/month

    BYD SEAL U / Ayvens
    48 months / 20,000 km/year
    245,990 HUF/month

    Opel Combo / Ayvens
    48 months / 20,000 km/year
    140,990 HUF/month

    BYD SEALION 7 / Ayvens
    48 months / 20,000 km/year
    251,990 HUF/month

No explicit common priced coordinate was found in these targeted runs, so all
four unique groups correctly remained INSUFFICIENT_EVIDENCE with no price
winner. Both Opel Combo offer pairs also evaluated successfully in full-market
run 9.

Full-market run 9 completed PARTIAL:

    candidate_count: 5
    evaluated_count: 2
    failed_count: 3
    price_comparable_count: 0

The three failures were provider navigation timeouts. Each affected BYD group
passed a targeted headed run, so these are classified as transient live-load
failures rather than contract-state regressions.

A subsequent bounded one-retry experiment produced run 10 with 0 evaluated
and 5 failed pairs. Failures spanned provider offer loading, BYD manufacturer
acquisition and Ayvens trim/API acquisition. The retry implementation was
therefore rejected and fully reverted.

## Validation work

1. Instrument pair/provider/stage timing without changing acquisition results.
2. Compare fresh-browser-per-pair behavior with the current sequential batch
   lifecycle and identify provider throttling or resource leakage.
3. Isolate optional manufacturer acquisition from core offer/contract loading
   in benchmark diagnostics.
4. Consider conservative pacing only after the responsible stage is known;
   do not add blind per-navigation retries.
5. Separately classify the historical deterministic suite's 19 failures into
   obsolete tests, mislabeled live tests, and current behavior regressions.
6. Modernize those tests in a separate focused patch; do not mix broad test
   cleanup into the Contract V3 change.

## Safety constraints

Do not:

- interpolate prices
- extrapolate prices
- apply provider term factors
- infer a price from an available duration/mileage option
- join unrelated JSON values
- assume missing evidence means zero
- declare nominal lower price a winner
- weaken FullComparisonOrchestrator blockers

Contract V3 must continue resolving only explicit common priced coordinates.

## Implementation expectation

Do not change comparison semantics in response to the benchmark. If a live
pair fails, classify provider schema, network, anti-bot, load, or genuine
evidence absence before editing code.

## Validation

Run relevant:

- py_compile checks
- deterministic resolver tests
- bridge/integration tests
- Contract V3 tests

Then run the relevant live test(s) if the environment permits.

Finally run the market benchmark if live provider access is healthy.

## Report

At completion report:

1. root cause
2. files changed
3. tests added or modified
4. deterministic test results
5. live test results
6. remaining provider/network failures
7. resulting Ayvens observations
8. whether common explicit priced coordinates were actually found
9. confirmation that comparison safety semantics were preserved

Do not claim success merely because price_comparable_count increased.

INSUFFICIENT_EVIDENCE remains a valid successful outcome when evidence is genuinely unavailable.
