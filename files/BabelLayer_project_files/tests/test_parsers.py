"""Tests for file parsers."""
from ingestion import load_file, profile_columns


class TestParsers:

    def test_load_csv(self, sample_csv):
        df = load_file(sample_csv)
        assert len(df) == 3
        assert "name" in df.columns

    def test_load_json(self, sample_json):
        df = load_file(sample_json)
        assert len(df) == 3
        assert "product" in df.columns

    def test_load_excel(self, sample_excel):
        df = load_file(sample_excel)
        assert len(df) == 3
        assert "employee_id" in df.columns

    def test_profile_columns(self, sample_csv):
        df = load_file(sample_csv)
        profile = profile_columns(df)
        assert len(profile) == 3
        assert all("name" in p for p in profile)
        assert all("dtype" in p for p in profile)

    def test_unsupported_format(self, tmp_path):
        bad = tmp_path / "test.xyz"
        bad.write_text("hello")
        import pytest
        with pytest.raises(ValueError):
            load_file(str(bad))
