"""
ETL execution engine.

Takes a list of field mappings and applies them to a source DataFrame
to produce a transformed output DataFrame.
"""
import pandas as pd
import logging
from dataclasses import dataclass
from typing import Any

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class MappingSpec:
    """Internal representation of one mapping rule."""

    source_field: str
    target_field: str
    mode: str = "direct"  # direct | transform | calculated
    rule: str | None = None


class TransformEngine:
    """Applies field mappings to transform a source DataFrame."""

    def __init__(self):
        self._mappings: list[MappingSpec] = []
        self._errors: list[str] = []

    def add(self, source_field: str, target_field: str,
            mode: str = "direct", rule: str = None):
        """Add one mapping rule.

        Kept as `add` for backwards compatibility with existing callers.
        """
        self._mappings.append(
            MappingSpec(
                source_field=source_field,
                target_field=target_field,
                mode=mode,
                rule=rule,
            )
        )

    def load(self, mapping_list: list[dict]):
        """Bulk-load mappings from a list of dicts."""
        self._mappings = [
            MappingSpec(
                source_field=m.get("source_field") or m.get("src"),
                target_field=m.get("target_field") or m.get("tgt"),
                mode=m.get("mode", "direct"),
                rule=m.get("rule"),
            )
            for m in mapping_list
        ]

    def run(self, source: pd.DataFrame) -> pd.DataFrame:
        """Execute all mappings against the source DataFrame."""
        self._errors = []
        output = pd.DataFrame(index=source.index)

        for spec in self._mappings:
            src, tgt = spec.source_field, spec.target_field
            try:
                if src not in source.columns:
                    raise KeyError(f"Source field '{src}' not found")

                if spec.mode == "transform" and spec.rule:
                    output[tgt] = self._apply_rule(source[src], spec.rule)
                elif spec.mode == "calculated" and spec.rule:
                    output[tgt] = self._eval_expression(source, spec.rule)
                else:
                    output[tgt] = source[src]

            except Exception as exc:
                msg = f"{src} → {tgt}: {exc}"
                log.error("Mapping error: %s", msg)
                self._errors.append(msg)

        log.info("Transform done: %d rows, %d cols, %d errors",
                 len(output), len(output.columns), len(self._errors))
        return output

    @property
    def errors(self):
        return list(self._errors)

    @property
    def stats(self):
        return {
            "total_mappings": len(self._mappings),
            "errors": len(self._errors),
            "error_messages": self._errors,
        }

    # -- Rule application -----------------------------------------------------

    @staticmethod
    def _apply_rule(series: pd.Series, rule: str) -> pd.Series:
        """Apply one safe transform rule to a single source series.

        Supported rules:
        - upper | lower | strip | title
        - replace:old:new
        - prefix:text
        - suffix:text
        """
        string_ops: dict[str, Any] = {
            "upper": lambda s: s.str.upper(),
            "lower": lambda s: s.str.lower(),
            "strip": lambda s: s.str.strip(),
            "title": lambda s: s.str.title(),
        }
        if rule in string_ops:
            return string_ops[rule](series)

        if rule.startswith("replace:"):
            _, old, new = rule.split(":", 2)
            return series.str.replace(old, new, regex=False)

        if rule.startswith("prefix:"):
            _, prefix = rule.split(":", 1)
            return prefix + series.astype(str)

        if rule.startswith("suffix:"):
            _, suffix = rule.split(":", 1)
            return series.astype(str) + suffix

        raise ValueError(
            "Unsupported transform rule. Use one of: "
            "upper, lower, strip, title, replace:old:new, prefix:text, suffix:text"
        )

    @staticmethod
    def _eval_expression(df: pd.DataFrame, expr: str) -> pd.Series:
        """Evaluate a calculated rule using an explicit mini-DSL.

        Supported rules:
        - add:col_a:col_b
        - sub:col_a:col_b
        - mul:col_a:col_b
        - div:col_a:col_b
        - copy:col
        """
        parts = expr.split(":")
        op = parts[0].strip().lower()

        if op == "copy" and len(parts) == 2:
            column = parts[1]
            return df[column]

        if op in {"add", "sub", "mul", "div"} and len(parts) == 3:
            left = df[parts[1]]
            right = df[parts[2]]
            if op == "add":
                return left + right
            if op == "sub":
                return left - right
            if op == "mul":
                return left * right
            return left / right

        raise ValueError(
            "Unsupported calculated rule. Use one of: "
            "copy:col, add:col_a:col_b, sub:col_a:col_b, mul:col_a:col_b, div:col_a:col_b"
        )
