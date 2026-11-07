import numpy as np
import pandas as pd
import pytest
from src.population import (
    asia_pop_life,
    asia_pop_total,
    build_population_matrix,
    generate_validation_rows,
    phil_pop_life,
    pop_ind,
    population_index,
    population_index_table,
)

@pytest.fixture
def standin_data():
    """Creates a small mock DataFrame to test functions without loading raw CSVs."""
    return pd.DataFrame(
        {
            "country": [
                "Philippines",
                "Philippines",
                "Indonesia",
                "Indonesia",
                "Thailand",
                "Thailand",
            ],
            "continent": ["Asia", "Asia", "Asia", "Asia", "Asia", "Asia"],
            "year": [1982, 2007, 1982, 2007, 1982, 2007],
            "lifeExp": [63.0, 71.0, 58.0, 70.0, 65.0, 74.0],
            "pop": [
                50000000,
                91077287,
                150000000,
                225000000,
                480000000,
                65000000,
            ],
        }
    )
def test_asia_pop_life(standin_data):
    """Verifies filtering, pop_millions creation, and lifeExp ranking."""
    result = asia_pop_life(standin_data, year=2007)

    assert len(result) == 3
    assert "pop_millions" in result.columns
    assert "lifeExp_rank" in result.columns
    # Country with highest life expectancy in 2007 (Thailand = 74.0) should be rank 1
    assert result.iloc[0]["country"] == "Thailand"
    assert result.iloc[0]["lifeExp_rank"] == 1

def test_asia_pop_total(standin_data):
    """Verifies the NumPy mask total and row count."""
    total, count = asia_pop_total(standin_data, year_arr=2007)

    assert total == 91077287 + 225000000 + 65000000
    assert count == 3
    # A continent with no rows gives zero total and zero rows
    assert asia_pop_total(standin_data, cont_arr="Europe", year_arr=2007) == (0, 0)

def test_phil_pop_life(standin_data):
    """Verifies baseline life expectancy change calculation."""
    result = phil_pop_life(standin_data, country="Philippines")

    assert len(result) == 2
    assert "lifeExp_change" in result.columns
    # First observed year (1982) must have change equal to 0.0
    assert result.iloc[0]["lifeExp_change"] == 0.0
    # Second year (2007: 71.0 - 63.0 = 8.0)
    assert result.iloc[1]["lifeExp_change"] == 8.0


def test_matrix_and_indexing(standin_data):
    """Verifies NumPy matrix construction and broadcast vs loop parity."""
    countries = ["Philippines", "Indonesia", "Thailand"]
    years = [1982, 2007]

    matrix = build_population_matrix(standin_data, countries, years)
    broadcast_idx = population_index(matrix)
    loop_idx = pop_ind(matrix)

    # Matrix shape check
    assert matrix.shape == (3, 2)
    # 1982 baseline column must equal 100.0 across all rows
    assert np.allclose(broadcast_idx[:, 0], 100.0)
    # Vectorized broadcasting and manual loops must yield identical results
    assert np.allclose(broadcast_idx, loop_idx, atol=1e-8)


def test_population_index_table(standin_data):
    """Verifies DataFrame conversion and error raising on mismatched shapes."""
    countries = ["Philippines", "Indonesia"]
    years = [1982, 2007]
    matrix = np.array([[100.0, 150.0], [100.0, 120.0]])

    table = population_index_table(matrix, countries, years)

    assert list(table.columns) == ["country", "1982", "2007"]
    assert table.iloc[0]["country"] == "Philippines"

    # Shape mismatch must raise ValueError
    with pytest.raises(ValueError):
        population_index_table(
            matrix, ["Philippines"], years
        )  # 2 rows expected, 1 given


def test_generate_validation_rows(standin_data):
    """Verifies that validation output returns a list of dictionaries with required keys."""
    countries = ["Philippines", "Indonesia", "Thailand"]
    years = [1982, 2007]

    results = generate_validation_rows(standin_data, countries, years)
    expected_keys = {"check", "expected", "actual", "tolerance", "pass"}

    assert isinstance(results, list)
    assert len(results) == 5
    for row in results:
        assert isinstance(row, dict)
        assert set(row.keys()) == expected_keys
