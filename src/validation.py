"""Row validation for the canonical country records."""

import math

from src.common import CANONICAL_COLUMNS 

def _is_finite_number(value):
    """Return True if value can be conveerted to a finite number."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False

    return math.isfinite(number)

def _is_integral_number(value):
    """Return True if value is finite and has no fractional part."""
    if not _is_finite_number(value):
        return False

    number = float(value)
    return number.is_integer()

ALLOWED_CONTINENTS = {
    "Africa",
    "Americas",
    "Asia",
    "Europe",
    "Oceania",
}

ALLOWED_YEARS = {
    1952, 1957, 1962, 1967, 1972, 1977,
    1982, 1987, 1992, 1997, 2002, 2007,
}

def validate_row(row):
    """Return a list of validation errors for one canonical row."""
    errors = []

    country = row.get("country")
    continent = row.get("continent")
    year = row.get("year")
    life_exp = row.get("lifeExp")
    population = row.get("pop")
    gdp_per_capita = row.get("gdpPercap")

    if country is None or not str(country).strip():
        errors.append("Country must be nonempty")
    if continent is None or not str(continent).strip():
        errors.append("Continent must be nonempty")
    elif str(continent).strip() not in ALLOWED_CONTINENTS:
        errors.append("Invalid continent")
    if not _is_integral_number(year):
        errors.append("Year must be a finite whole number")
    elif int(float(year)) not in ALLOWED_YEARS:
        errors.append("Year is not allowed")
    if not _is_finite_number(life_exp):
        errors.append("Life expectancy must be a finite number")
    elif not 0 < float(life_exp) <= 120:
        errors.append("Life expectancy must be greater than 0 and at most 120")
    if not _is_integral_number(population):
        errors.append("Population must be a finite whole number")
    elif int(float(population)) <= 0:
        errors.append("Population must be greater than 0")
    if not _is_finite_number(gdp_per_capita):
        errors.append("GDP per capita must be a finite number")
    elif float(gdp_per_capita) <= 0:
        errors.append("GDP per capita must be greater than 0")
    return errors 

