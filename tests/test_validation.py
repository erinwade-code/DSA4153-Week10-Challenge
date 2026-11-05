"""Tests for row validation."""

from src.validation import validate_row


def test_valid_row_has_no_errors():
    row = {
        "country": "Philippines",
        "continent": "Asia",
        "year": "2007",
        "lifeExp": "71.0",
        "pop": "91077287",
        "gdpPercap": "3190.0",
    }

    assert validate_row(row) == []

def test_invalid_continent_is_rejected():
    row = {
        "country": "Philippines",
        "continent": "Atlantis",
        "year": "2007",
        "lifeExp": "71.0",
        "pop": "91077287",
        "gdpPercap": "3190.0",
    }

    errors = validate_row(row)

    assert "Invalid continent" in errors


def test_disallowed_year_is_rejected():
    row = {
        "country": "Philippines",
        "continent": "Asia",
        "year": "2005",
        "lifeExp": "71.0",
        "pop": "91077287",
        "gdpPercap": "3190.0",
    }

    errors = validate_row(row)

    assert "Year is not allowed" in errors

def test_invalid_life_expectancy_is_rejected():
    row = {
        "country": "Philippines",
        "continent": "Asia",
        "year": "2007",
        "lifeExp": "130",
        "pop": "91077287",
        "gdpPercap": "3190.0",
    }

    errors = validate_row(row)

    assert (
        "Life expectancy must be greater than 0 and at most 120"
        in errors
    )

def test_invalid_population_is_rejected():
    row = {
        "country": "Philippines",
        "continent": "Asia",
        "year": "2007",
        "lifeExp": "71.0",
        "pop": "0",
        "gdpPercap": "3190.0",
    }

    errors = validate_row(row)

    assert "Population must be greater than 0" in errors

def test_invalid_gdp_per_capita_is_rejected():
    row = {
        "country": "Philippines",
        "continent": "Asia",
        "year": "2007",
        "lifeExp": "71.0",
        "pop": "91077287",
        "gdpPercap": "0",
    }

    errors = validate_row(row)

    assert "GDP per capita must be greater than 0" in errors


def test_non_numeric_life_expectancy_is_rejected():
    row = {
        "country": "Philippines",
        "continent": "Asia",
        "year": "2007",
        "lifeExp": "unknown",
        "pop": "91077287",
        "gdpPercap": "3190.0",
    }

    errors = validate_row(row)

    assert "Life expectancy must be a finite number" in errors

def test_empty_country_is_rejected():
    row = {
        "country": "   ",
        "continent": "Asia",
        "year": "2007",
        "lifeExp": "71.0",
        "pop": "91077287",
        "gdpPercap": "3190.0",
    }

    errors = validate_row(row)

    assert "Country must be nonempty" in errors