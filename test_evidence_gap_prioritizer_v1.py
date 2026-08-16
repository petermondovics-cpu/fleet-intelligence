from comparison.evidence_gap_prioritizer_v1 import EvidenceGapPrioritizerV1

def main():
    reasons=("VEHICLE_VARIANT_DIFFERENCE","VARIANT_VALUE_DIFFERENCE","SERVICE_PARTIAL_EQUIVALENCE","EQUIPMENT_VALUE_DIFFERENCE","NO_COMMON_PRICED_CONTRACT_STATE","DOWN_PAYMENT_EVIDENCE_INCOMPLETE")
    plan=EvidenceGapPrioritizerV1().prioritize(reasons)
    assert tuple(x.dimension for x in plan.actions)==("CONTRACT","FINANCIAL","SERVICES","EQUIPMENT_VARIANT")
    assert tuple(x.impact for x in plan.actions)==("CRITICAL","CRITICAL","HIGH","HIGH")
    assert [x.price_comparison_may_be_possible for x in plan.unlock_path]==[False,False,False,True]
    print("TEST PASSED - PRIORITIZED EVIDENCE PLAN AND CONDITIONAL UNLOCK PATH ARE CORRECT.")

if __name__=="__main__":
    main()
