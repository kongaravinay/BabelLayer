"""
ETL execution engine.

Takes a list of field mappings and applies them to a source DataFrame
to produce a transformed output DataFrame.
"""
import pandas as pd
import logging

log = logging.getLogger(__name__)


class TransformEngine:
    """Applies field mappings to transform a source DataFrame."""

    def __init__(self):
        self._mappings = []
        self._errors = []

    def add(self, source_field: str, target_field: str,
            mode: str = "direct", rule: str = None):
        self._mappings.append({
            "src": source_field,
            "tgt": target_field,
            "mode": mode,     # direct | transform | calculated
            "rule": rule,
        })

    def load(self, mapping_list: list[dict]):
        """Bulk-load mappings from a list of dicts."""
        self._mappings = mapping_list

    def run(self, source: pd.DataFrame) -> pd.DataFrame:
        """Execute all mappings against the source DataFrame."""
        self._errors = []
        out = pd.DataFrame()

        for m in self._mappings:
            src, tgt = m["src"], m["tgt"]
            try:
                if src not in source.columns:
                    raise KeyError(f"Source field '{src}' not found")

                if m["mode"] == "transform" and m["rule"]:
                    out[tgt] = self._apply_rule(source[src], m["rule"])
                elif m["mode"] == "calculated" and m["rule"]:
                    out[tgt] = self._eval_expression(source, m["rule"])
                else:
                    out[tgt] = source[src]

            except Exception as exc:
                msg = f"{src} → {tgt}: {exc}"
                log.error("Mapping error: %s", msg)
                self._errors.append(msg)

        log.info("Transform done: %d rows, %d cols, %d errors",
                 len(out), len(out.columns), len(self._errors))
        return out

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
        builtins = {
            "upper": lambda s: s.str.upper(),
            "lower": lambda s: s.str.lower(),
            "strip": lambda s: s.str.strip(),
        }
        if rule in builtins:
            return builtins[rule](series)

        if rule.startswith("replace:"):
            _, old, new = rule.split(":", 2)
            return series.str.replace(old, new, regex=False)

        # Generic expression — restricted builtins for safety
        safe = {"series": series, "pd": pd, "str": str, "int": int, "float": float}
        return eval(rule, {"__builtins__": {}}, safe)

    @staticmethod
    def _eval_expression(df: pd.DataFrame, expr: str) -> pd.Series:
        safe = {"df": df, "pd": pd}
        return eval(expr, {"__builtins__": {}}, safe)
