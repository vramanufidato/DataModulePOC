"""
Run a Great Expectations checkpoint.
Usage:
    python run_checkpoint.py silver_orders_checkpoint
    python run_checkpoint.py gold_revenue_checkpoint

Exits with code 1 on failure (for CI/CD integration).
"""
from __future__ import annotations

import os
import sys

import great_expectations as gx

def main() -> int:
    checkpoint_name = sys.argv[1] if len(sys.argv) > 1 else "silver_orders_checkpoint"
    context = gx.get_context(context_root_dir=os.path.dirname(__file__))

    result = context.run_checkpoint(checkpoint_name=checkpoint_name)

    if not result.success:
        print(f"❌ Checkpoint {checkpoint_name} FAILED")
        for r in result.list_validation_results():
            for res in r.results:
                if not res.success:
                    print(f"  ✗ {res.expectation_config.expectation_type} "
                          f"({res.expectation_config.kwargs})")
        return 1

    print(f"✅ Checkpoint {checkpoint_name} PASSED")
    for r in result.list_validation_results():
        print(f"  → {len(r.results)} expectations, "
              f"{r.statistics['successful_expectations']} passed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
