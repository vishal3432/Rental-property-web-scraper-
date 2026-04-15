"""Tests for HTML parser."""

import pytest
from app.scraper.parser import parse_properties, validate_price, validate_address, validate_link


def test_parse_properties_valid(sample_html):
    """Test parsing valid HTML."""
    properties = parse_properties(sample_html)
    assert len(properties) > 0
    
    for prop in properties:
        assert "address" in prop
        assert "price_text" in prop
        assert "price_value" in prop
        assert "link" in prop


def test_parse_properties_empty_html():
    """Test parsing empty HTML."""
    properties = parse_properties("")
    assert properties == []


def test_parse_properties_invalid_html():
    """Test parsing invalid HTML (no expected selectors)."""
    invalid_html = "<html><body>No properties here</body></html>"
    properties = parse_properties(invalid_html)
    assert properties == []


def test_parse_properties_none():
    """Test parsing None."""
    properties = parse_properties(None)
    assert properties == []


def test_validate_price_valid():
    """Test price validation with valid prices."""
    assert validate_price("$1,500/mo") == 1500.0
    assert validate_price("$2000.50") == 2000.50
    assert validate_price("$1000") == 1000.0


def test_validate_price_invalid():
    """Test price validation with invalid prices."""
    assert validate_price("") == 0.0
    assert validate_price(None) == 0.0
    assert validate_price("no number") == 0.0
    assert validate_price("$-500") == 0.0  # Negative
    assert validate_price("$1000000000") == 0.0  # Too high


def test_validate_address_valid():
    """Test address validation with valid addresses."""
    assert validate_address("123 Main St") == "123 Main St"
    assert validate_address("456 Oak Ave | City") == "456 Oak Ave City"
    assert validate_address("  789 Elm St  ") == "789 Elm St"


def test_validate_address_invalid():
    """Test address validation with invalid addresses."""
    assert validate_address("") == ""
    assert validate_address(None) == ""
    assert validate_address("a") == ""  # Too short
    assert validate_address("x" * 300) == ""  # Too long


def test_validate_link_valid():
    """Test link validation with valid links."""
    assert validate_link("/property/123") == "/property/123"
    assert validate_link("https://example.com/property") == "https://example.com/property"
    assert validate_link("http://example.com") == "http://example.com"


def test_validate_link_invalid():
    """Test link validation with invalid links."""
    assert validate_link("") == ""
    assert validate_link(None) == ""
    assert validate_link("not a link") == ""
    assert validate_link("x" * 3000) == ""  # Too long
