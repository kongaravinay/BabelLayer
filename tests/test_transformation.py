"""Tests for data transformation engine."""
import pandas as pd
from transformation.engine import Transformer
from transformation.validator import Validator


class TestTransformer:

    def test_direct_mapping(self):
        src = pd.DataFrame({"name": ["Alice", "Bob"], "age": [30, 25]})
        engine = Transformer()
        engine.add("name", "full_name")
        engine.add("age", "years")
        result = engine.run(src)
        assert "full_name" in result.columns
        assert "years" in result.columns
        assert len(result) == 2

    def test_missing_source_field(self):
        src = pd.DataFrame({"name": ["Alice"]})
        engine = Transformer()
        engine.add("missing_field", "target")
        result = engine.run(src)
        assert len(engine.errors) > 0

    def test_upper_rule(self):
        src = pd.DataFrame({"name": ["alice", "bob"]})
        engine = Transformer()
        engine.add("name", "NAME", "transform", "upper")
        result = engine.run(src)
        assert result["NAME"].tolist() == ["ALICE", "BOB"]

    def test_stats(self):
        src = pd.DataFrame({"x": [1, 2]})
        engine = Transformer()
        engine.add("x", "y")
        engine.run(src)
        assert engine.stats["total_mappings"] == 1
        assert engine.stats["errors"] == 0


class TestValidator:

    def test_not_null_pass(self):
        df = pd.DataFrame({"name": ["A", "B"]})
        result = Validator().require_not_null("name").check(df)
        assert result["valid"] is True

    def test_not_null_fail(self):
        df = pd.DataFrame({"name": ["A", None]})
        result = Validator().require_not_null("name").check(df)
        assert result["valid"] is False
        assert len(result["violations"]) == 1

    def test_range_check(self):
        df = pd.DataFrame({"age": [10, 25, 150]})
        result = Validator().require_range("age", min_val=0, max_val=120).check(df)
        assert result["valid"] is False
