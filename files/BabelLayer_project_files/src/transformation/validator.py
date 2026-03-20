"""
Row-level data validation.

Use when you need to enforce constraints (not-null, value ranges, etc.)
before running a transformation.
"""
import pandas as pd
import logging

log = logging.getLogger(__name__)


class Validator:

    def __init__(self):
        self._rules = []

    def require_not_null(self, field: str):
        self._rules.append({"field": field, "type": "not_null"})
        return self  # chainable

    def require_range(self, field: str, *, min_val=None, max_val=None):
        self._rules.append({"field": field, "type": "range", "min": min_val, "max": max_val})
        return self

    def check(self, df: pd.DataFrame) -> dict:
        """Run all rules. Returns {valid: bool, violations: [...]}}."""
        violations = []

        for r in self._rules:
            field = r["field"]
            if field not in df.columns:
                violations.append({"field": field, "rule": r["type"],
                                   "message": f"Field '{field}' missing"})
                continue

            if r["type"] == "not_null":
                n = int(df[field].isnull().sum())
                if n:
                    violations.append({"field": field, "rule": "not_null",
                                       "message": f"{n} null values", "count": n})

            elif r["type"] == "range":
                if r.get("min") is not None:
                    below = len(df[df[field] < r["min"]])
                    if below:
                        violations.append({"field": field, "rule": "range_min",
                                           "message": f"{below} below {r['min']}", "count": below})
                if r.get("max") is not None:
                    above = len(df[df[field] > r["max"]])
                    if above:
                        violations.append({"field": field, "rule": "range_max",
                                           "message": f"{above} above {r['max']}", "count": above})

        log.info("Validation: %d violations across %d rules", len(violations), len(self._rules))
        return {"valid": len(violations) == 0, "violations": violations}
