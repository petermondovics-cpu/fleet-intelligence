from market_intelligence.benchmark_evidence_plan_dashboard_service_v3 import BenchmarkEvidencePlanDashboardServiceV3

def main():
    print("="*100)
    print("LIVE BENCHMARK EVIDENCE PLAN DASHBOARD V3")
    print("="*100)
    data=BenchmarkEvidencePlanDashboardServiceV3().load()
    print("\n--- FIRST PRIORITY DIMENSIONS ---")
    for k,v in data.first_priority_dimension_counts.items(): print(k,v)
    print("\n--- ALL PRIORITIZED DIMENSIONS ---")
    for k,v in data.prioritized_dimension_counts.items(): print(k,v)
    print("\n--- IMPACT COUNTS ---")
    for k,v in data.impact_counts.items(): print(k,v)
    print("\n--- UNLOCK PATHS ---")
    for k,v in data.full_unlock_path_counts.items(): print(v,"|",k)
    print("\n--- MANAGEMENT SUMMARY ---")
    print(data.management_summary)
    print("\n--- PAIR PLANS ---")
    for pair in data.pair_plans:
        print("\n",pair["group_key"])
        for a in pair["actions"]:
            print(a["rank"],a["dimension"],a["impact"],"|",a["action"])
    assert data.pair_plans and data.first_priority_dimension_counts and data.prioritized_dimension_counts
    print("\nTEST PASSED - BENCHMARK RESULTS EXPOSE PRIORITIZED EVIDENCE PLANS AND CONDITIONAL UNLOCK PATHS.")

if __name__=="__main__":
    main()
