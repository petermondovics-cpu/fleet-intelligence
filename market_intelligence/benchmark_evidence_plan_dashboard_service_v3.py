from dataclasses import asdict, dataclass
from typing import Dict, Tuple
from comparison.evidence_gap_prioritizer_v1 import EvidenceGapPrioritizerV1
from market_intelligence.benchmark_decision_dashboard_service_v2 import BenchmarkDecisionDashboardServiceV2
from market_intelligence.benchmark_read_repository import BenchmarkReadRepository

@dataclass(frozen=True)
class BenchmarkEvidencePlanDashboardDataV3:
    base: dict
    prioritized_dimension_counts: Dict[str,int]
    first_priority_dimension_counts: Dict[str,int]
    impact_counts: Dict[str,int]
    full_unlock_path_counts: Dict[str,int]
    pair_plans: Tuple[dict,...]
    management_summary: str

class BenchmarkEvidencePlanDashboardServiceV3:
    def __init__(self, repository=None):
        self.repository=repository or BenchmarkReadRepository()
        self.prioritizer=EvidenceGapPrioritizerV1()

    def load(self):
        base=BenchmarkDecisionDashboardServiceV2(repository=self.repository).load()
        rows=self.repository.results_for_run(base.run["id"]) if base.run else ()
        dims={}; firsts={}; impacts={}; paths={}; pair_plans=[]
        for row in rows:
            response=row.response if isinstance(row.response,dict) else {}
            decision=response.get("decision")
            decision=decision if isinstance(decision,dict) else {}
            plan=self.prioritizer.prioritize(decision.get("decision_reasons") or ())
            for a in plan.actions:
                dims[a.dimension]=dims.get(a.dimension,0)+1
                impacts[a.impact]=impacts.get(a.impact,0)+1
            if plan.actions:
                d=plan.actions[0].dimension
                firsts[d]=firsts.get(d,0)+1
            key=" -> ".join(a.dimension for a in plan.actions) or "NO_ACTION"
            paths[key]=paths.get(key,0)+1
            pair_plans.append({
                "pair_key":row.pair_key,
                "group_key":row.group_key,
                "actions":tuple(a.to_dict() for a in plan.actions),
                "unlock_path":tuple(s.to_dict() for s in plan.unlock_path),
                "diagnostic":plan.diagnostic,
            })
        summary=self._summary(base,firsts,dims)
        return BenchmarkEvidencePlanDashboardDataV3(
            base=asdict(base),
            prioritized_dimension_counts=self._sort(dims),
            first_priority_dimension_counts=self._sort(firsts),
            impact_counts=self._sort(impacts),
            full_unlock_path_counts=self._sort(paths),
            pair_plans=tuple(pair_plans),
            management_summary=summary,
        )

    @staticmethod
    def _sort(d): return dict(sorted(d.items(),key=lambda x:(-x[1],x[0])))

    @staticmethod
    def _summary(base,firsts,dims):
        if not base.pair_count: return "No benchmark pair results are available."
        parts=[f"{base.pair_count} benchmark pairs across {base.group_count} vehicle groups were analyzed.",f"{base.price_comparable_count}/{base.pair_count} are currently safe for price ranking."]
        if firsts:
            k,v=sorted(firsts.items(),key=lambda x:(-x[1],x[0]))[0]
            parts.append(f"The highest-priority evidence dimension is {k} for {v} pairs.")
        if dims:
            parts.append("Resolving the first priority alone does not imply price comparability; the full remaining evidence path must also be cleared.")
        return " ".join(parts)
