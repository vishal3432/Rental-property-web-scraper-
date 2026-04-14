import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup


class ParseError(ValueError):
    pass


def _is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)


def parse_properties(html: str) -> list[dict]:
    if not html or len(html) < 200:
        raise ParseError("HTML payload too short; scraping target may be blocked or changed")

    soup = BeautifulSoup(html, "html.parser")
    links = [link.get("href") for link in soup.select(".StyledPropertyCardDataWrapper a") if link.get("href")]
    addresses = [
        node.get_text().replace(" | ", " ").strip()
        for node in soup.select(".StyledPropertyCardDataWrapper address")
    ]
    prices = [
        node.get_text().replace("/mo", "").split("+")[0].strip()
        for node in soup.select(".PropertyCardWrapper span")
        if "$" in node.get_text()
    ]

    if not (links and addresses and prices):
        raise ParseError("Required listing selectors not found in HTML")

    items: list[dict] = []
    for address, price_text, link in zip(addresses, prices, links, strict=False):
        if not address or not price_text or not _is_valid_url(link):
            continue
        numeric = re.sub(r"[^0-9.]", "", price_text)
        if not numeric:
            continue
        items.append(
            {
                "address": address,
                "price_text": price_text,
                "price_value": float(numeric),
                "link": link,
            }
        )

    if not items:
        raise ParseError("No valid listings could be parsed")
    return items
