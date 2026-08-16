from dataclasses import dataclass
from comparison.variant_equivalence_assessor import *

@dataclass
class Item:
    name: str
    included: bool = True
@dataclass
class Vehicle:
    trim: str
    all_equipment: tuple
@dataclass
class Composite:
    vehicle: Vehicle
@dataclass
class Evidence:
    fully_comparable: bool
@dataclass
class Side:
    composite: Composite
    equipment_evidence: Evidence

def side(trim, names, complete=True):
    return Side(Composite(Vehicle(trim, tuple(Item(x) for x in names))),
                Evidence(complete))

def main():
    e = VariantEquivalenceAssessor()
    left = side("Boost", ("fűthető kormánykerék",), True)
    right = side("Active", ("fűthető kormánykerék",), False)
    assert e.assess(left, right, "COMPARABLE").status == VARIANT_INSUFFICIENT_EVIDENCE
    print("TEST 1 PASSED - ONE-SIDED EVIDENCE BLOCKED")

    right = side("Active", ("fűthető kormánykerék",), True)
    r = e.assess(left, right, "COMPARABLE")
    assert r.status == VARIANT_EQUIVALENT and r.equipment_comparison.score_delta == 0
    print("TEST 2 PASSED - FULLY SCORED EQUAL VALUE")

    right = side("Active", ("fűthető kormánykerék", "tolatókamera"), True)
    assert e.assess(left, right, "COMPARABLE").status == VARIANT_VALUE_DIFFERENCE
    print("TEST 3 PASSED - VALUE DIFFERENCE PRESERVED")

    right = side("Active", ("mystery laser comfort package",), True)
    assert e.assess(left, right, "COMPARABLE").status == VARIANT_INSUFFICIENT_EVIDENCE
    print("TEST 4 PASSED - UNKNOWN ITEM BLOCKS")

    same = side("Boost", (), False)
    assert e.assess(left, same, "COMPARABLE").status == VARIANT_EQUIVALENT
    print("TEST 5 PASSED - SAME TRIM NEEDS NO VARIANT PROOF")

    assert e.assess(left, right, "NOT_COMPARABLE").status == VARIANT_NOT_EQUIVALENT
    print("TEST 6 PASSED - IDENTITY MISMATCH HARD")
    print("\nALL VARIANT EQUIVALENCE ASSESSMENT V1 TESTS PASSED")

if __name__ == "__main__":
    main()
