import re
from bs4 import BeautifulSoup


def parse_properties(html: str) -> list[dict]:
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

    items: list[dict] = []
    for address, price_text, link in zip(addresses, prices, links, strict=False):
        numeric = re.sub(r"[^0-9.]", "", price_text)
        price_value = float(numeric) if numeric else 0.0
        items.append(
            {
                "address": address,
                "price_text": price_text,
                "price_value": price_value,
                "link": link,
            }
        )
    return items
