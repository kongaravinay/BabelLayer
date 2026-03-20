"""Tests for schema mapper."""
import pytest
from ai.schema_mapper import FieldMatcher


@pytest.fixture(scope="module")
def mapper():
    return FieldMatcher()


class TestFieldMatcher:

    def test_similar_fields(self, mapper):
        score = mapper.field_similarity("customer_name", "client_name")
        assert score > 0.5

    def test_unrelated_fields(self, mapper):
        score = mapper.field_similarity("email_address", "quantity_sold")
        assert score < 0.7

    def test_identical_fields(self, mapper):
        score = mapper.field_similarity("status", "status")
        assert score > 0.95

    def test_suggest_mappings(self, mapper):
        source = ["customer_name", "email", "phone_number"]
        target = ["client_name", "email_address", "telephone"]
        results = mapper.suggest_mappings(source, target)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_mapping_keys(self, mapper):
        results = mapper.suggest_mappings(["customer_name"], ["client_name"])
        if results:
            r = results[0]
            assert "source_field" in r
            assert "target_field" in r
            assert "confidence" in r

    def test_empty_input(self, mapper):
        assert mapper.suggest_mappings([], []) == []
