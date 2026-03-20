"""Shared test fixtures."""
import sys
from pathlib import Path
import pytest
import pandas as pd

# Let tests import from src/
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_csv(tmp_path):
    df = pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [30, 25, 35],
        "email": ["alice@test.com", "bob@test.com", "charlie@test.com"],
    })
    p = tmp_path / "test.csv"
    df.to_csv(p, index=False)
    return str(p)


@pytest.fixture
def sample_json(tmp_path):
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "product": ["Widget", "Gadget", "Doohickey"],
        "price": [9.99, 24.95, 14.50],
    })
    p = tmp_path / "test.json"
    df.to_json(p, orient="records", indent=2)
    return str(p)


@pytest.fixture
def sample_excel(tmp_path):
    df = pd.DataFrame({
        "employee_id": [101, 102, 103],
        "department": ["Sales", "Engineering", "HR"],
        "salary": [55000, 95000, 62000],
    })
    p = tmp_path / "test.xlsx"
    df.to_excel(p, index=False)
    return str(p)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "customer_name": ["John Smith", "Jane Doe", "Bob Wilson"] * 50,
        "age": [30, 25, 45] * 50,
        "income": [50000, 75000, 90000] * 50,
        "city": ["Houston", "Dallas", "Austin"] * 50,
    })


@pytest.fixture
def outlier_df():
    """DataFrame with intentional outliers for anomaly detection."""
    normal = pd.DataFrame({"value": list(range(50, 150)), "cat": ["A", "B", "C", "D"] * 25})
    outliers = pd.DataFrame({"value": [9999, -500, 10000], "cat": ["A", "B", "C"]})
    return pd.concat([normal, outliers], ignore_index=True)
