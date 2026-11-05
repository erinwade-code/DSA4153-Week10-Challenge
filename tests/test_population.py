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
