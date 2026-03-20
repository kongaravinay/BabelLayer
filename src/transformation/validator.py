"""
Row-level data validation.

Use when you need to enforce constraints (not-null, value ranges, etc.)
before running a transformation.
"""
import pandas as pd
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidationRule:
    """Internal validation rule definition."""

    field: str
    kind: str
    min_val: float | None = None
    max_val: float | None = None


class Validator:
    """Fluent validator for tabular data."""

    def __init__(self):
        self._rules: list[ValidationRule] = []

    def require_not_null(self, field: str):
        self._rules.append(ValidationRule(field=field, kind="not_null"))
        return self  # chainable

    def require_range(self, field: str, *, min_val=None, max_val=None):
        self._rules.append(
            ValidationRule(field=field, kind="range", min_val=min_val, max_val=max_val)
        )
        return self

    def check(self, df: pd.DataFrame) -> dict:
        """Run all rules. Returns {valid: bool, violations: [...]}}."""
        violations: list[dict] = []

        for rule in self._rules:
            field = rule.field
            if field not in df.columns:
                violations.append({"field": field, "rule": rule.kind,
                                   "message": f"Field '{field}' missing"})
                continue

            if rule.kind == "not_null":
                null_count = int(df[field].isnull().sum())
                if null_count:
                    violations.append({"field": field, "rule": "not_null",
                                       "message": f"{null_count} null values", "count": null_count})

            elif rule.kind == "range":
                if rule.min_val is not None:
                    below = len(df[df[field] < rule.min_val])
                    if below:
                        violations.append({"field": field, "rule": "range_min",
                                           "message": f"{below} below {rule.min_val}", "count": below})
                if rule.max_val is not None:
                    above = len(df[df[field] > rule.max_val])
                    if above:
                        violations.append({"field": field, "rule": "range_max",
                                           "message": f"{above} above {rule.max_val}", "count": above})

        log.info("Validation: %d violations across %d rules", len(violations), len(self._rules))
        return {"valid": len(violations) == 0, "violations": violations}
