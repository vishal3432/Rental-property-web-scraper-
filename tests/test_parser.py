import pytest

from app.scraper.parser import ParseError, parse_properties


def test_parse_properties_success():
    html = '''
    <html><body>
    <div class="StyledPropertyCardDataWrapper">
      <a href="https://example.com/1">listing</a>
      <address>123 Main St | Apt 1</address>
    </div>
    <div class="PropertyCardWrapper"><span>$1200/mo</span></div>
    </body></html>
    '''
    rows = parse_properties(html)
    assert len(rows) == 1
    assert rows[0]["price_value"] == 1200.0


def test_parse_properties_invalid_html():
    with pytest.raises(ParseError):
        parse_properties("<html></html>")
