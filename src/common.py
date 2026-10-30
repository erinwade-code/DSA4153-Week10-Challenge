"""Shared constants and errors."""

CANONICAL_COLUMNS = ["country", "continent", "year", "lifeExp", "pop", "gdpPercap"]

class FileLevelError(Exception):
    """Raised for file/schema problems that must stop processing."""