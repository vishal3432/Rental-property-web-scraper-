"""Backward-compatible entrypoint for scraping pipeline."""

from app.core.config import get_settings
from app.scraper.http_client import ScraperClient
from app.scraper.parser import parse_properties


def run_scraper() -> list[dict]:
    settings = get_settings()
    html = ScraperClient().get(settings.scrape_url)
    return parse_properties(html)
