"""
tests/unit/test_slug.py
-----------------------
Unit tests for the slug generation utility.

Unit tests test a single function in isolation - no database, no HTTP requests.
They run very fast and catch logic errors early.
"""

import pytest
from app.utils.slug import generate_slug


def test_basic_slug():
    """Normal title converts to hyphenated lowercase."""
    assert generate_slug("My First Article") == "my-first-article"


def test_slug_with_special_chars():
    """Special characters are removed or replaced."""
    assert generate_slug("Hello, World!") == "hello-world"


def test_slug_with_numbers():
    """Numbers are preserved in slugs."""
    assert generate_slug("Top 10 Python Tips") == "top-10-python-tips"


def test_slug_with_accents():
    """Accented characters are transliterated to ASCII."""
    result = generate_slug("Café au lait")
    assert result == "cafe-au-lait"


def test_slug_with_multiple_spaces():
    """Multiple spaces are collapsed to single hyphens."""
    result = generate_slug("Hello   World")
    assert result == "hello-world"


def test_slug_all_special():
    """A title of only special chars produces an empty or safe slug."""
    result = generate_slug("!!! ???")
    # Should not crash; result may be empty or have safe chars
    assert isinstance(result, str)
