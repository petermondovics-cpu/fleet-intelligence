from types import SimpleNamespace
from market_intelligence.benchmark_decision_dashboard_service_v2 import BenchmarkDecisionDashboardServiceV2

def make_row(pair_key, group_key, lower_provider, diff_huf, diff_pct, reasons):
    return SimpleNamespace(
        id=1, run_id=7, pair_key=pair_key, group_key=group_key,
        pair_status="NORMALIZABLE_PAIR", brand="BYD", model="ATTO 2", fuel_type="PHEV",
        left_provider="Arval", right_provider="Ayvens", bridge_status="EVALUATED",
        comparison_status="INSUFFICIENT_EVIDENCE", price_comparison_allowed=False,
        price_winner=None, left_advertised_monthly_fee_huf=192312,
        right_advertised_monthly_fee_huf=189990, left_comparable_monthly_fee_huf=None,
        right_comparable_monthly_fee_huf=None, blocker_count=2,
        blockers=({"code":"CONTRACT_NORMALIZATION_INCOMPLETE"},{"code":"DOWN_PAYMENT_EVIDENCE_INCOMPLETE"}),
        response={"api_version":"comparison.v2","decision":{
            "verdict":"INSUFFICIENT_EVIDENCE",
            "observed_price_difference":{"lower_provider":lower_provider,"difference_huf":diff_huf,"difference_percent":diff_pct,"normalized":False},
            "decision_reasons":reasons,
            "next_best_action":"Obtain one exact explicitly priced contract coordinate."
        }},
        diagnostic="", observed_at="2026-08-16T00:00:00"
    )

class Repo:
    def latest_run(self):
        return SimpleNamespace(id=7, started_at="x", completed_at="y", status="COMPLETED", candidate_count=2, evaluated_count=2, failed_count=0, price_comparable_count=0, diagnostic="")
    def results_for_run(self, run_id):
        return (
            make_row("p1","BYD::ATTO 2::PHEV","Ayvens",2322,1.21,("NO_COMMON_PRICED_CONTRACT_STATE","DOWN_PAYMENT_EVIDENCE_INCOMPLETE")),
            make_row("p2","BYD::SEAL U::PHEV","Arval",5000,2.5,("NO_COMMON_PRICED_CONTRACT_STATE",)),
        )

def main():
    result = BenchmarkDecisionDashboardServiceV2(repository=Repo()).load()
    assert result.pair_count == 2
    assert result.group_count == 2
    assert result.evaluated_rate == 100.0
    assert result.price_comparable_rate == 0.0
    assert result.verdict_counts == {"INSUFFICIENT_EVIDENCE": 2}
    assert result.decision_reason_counts["NO_COMMON_PRICED_CONTRACT_STATE"] == 2
    assert result.observed_lower_provider_counts == {"Arval": 1, "Ayvens": 1}
    assert result.average_nominal_difference_huf == 3661
    assert result.average_nominal_difference_percent == 1.85
    assert "not a normalized price-win count" in result.management_summary
    print("TEST PASSED - DECISION DASHBOARD V2 AGGREGATES PERSISTED COMPARISON.V2 DATA WITHOUT RECOMPUTING WINNERS.")

if __name__ == "__main__":
    main()
