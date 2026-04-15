import re
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def validate_html(html: str) -> bool:
    """Validate that HTML content is not empty and contains expected structure."""
    if not html or not isinstance(html, str):
        logger.warning("Invalid HTML: content is empty or not a string")
        return False
    
    if len(html.strip()) < 100:
        logger.warning("Invalid HTML: content too short (< 100 characters)")
        return False
    
    if "StyledPropertyCardDataWrapper" not in html and "PropertyCardWrapper" not in html:
        logger.warning("Invalid HTML: expected selectors not found - website structure may have changed")
        return False
    
    return True


def validate_price(price_text: str) -> float:
    """Validate and convert price text to float."""
    if not price_text or not isinstance(price_text, str):
        logger.debug(f"Invalid price text: {price_text}")
        return 0.0
    
    # Remove common price formatting
    cleaned = price_text.replace("/mo", "").split("+")[0].strip()
    
    # Extract numeric value
    numeric = re.sub(r"[^0-9.]", "", cleaned)
    
    if not numeric:
        logger.debug(f"Could not extract numeric value from: {price_text}")
        return 0.0
    
    try:
        price_value = float(numeric)
        
        # Sanity check - reject unrealistic prices
        if price_value < 0 or price_value > 999999:
            logger.debug(f"Price out of realistic range: {price_value}")
            return 0.0
        
        return price_value
    except ValueError as e:
        logger.debug(f"Could not convert price to float: {numeric} - {e}")
        return 0.0


def validate_address(address: str) -> str:
    """Validate and clean address text."""
    if not address or not isinstance(address, str):
        logger.debug(f"Invalid address: {address}")
        return ""
    
    cleaned = address.replace(" | ", " ").strip()
    
    # Reject obviously invalid addresses
    if len(cleaned) < 3 or len(cleaned) > 255:
        logger.debug(f"Address length out of range: {len(cleaned)}")
        return ""
    
    return cleaned


def validate_link(link: str) -> str:
    """Validate URL/link format."""
    if not link or not isinstance(link, str):
        logger.debug(f"Invalid link: {link}")
        return ""
    
    link = link.strip()
    
    # Should be a relative or absolute URL
    if not (link.startswith("/") or link.startswith("http") or link.startswith("#")):
        logger.debug(f"Link does not match expected format: {link}")
        return ""
    
    if len(link) > 2048:  # Max URL length
        logger.debug(f"Link too long: {len(link)} characters")
        return ""
    
    return link


def parse_properties(html: str) -> list[dict]:
    """
    Parse rental properties from HTML content.
    
    Args:
        html: HTML content as string
        
    Returns:
        List of property dictionaries with address, price_text, price_value, and link
        
    Raises:
        ValueError: If HTML content is invalid or missing expected structure
    """
    # Validate input
    if not validate_html(html):
        logger.error("HTML validation failed - website structure may have changed")
        return []
    
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception as e:
        logger.error(f"Failed to parse HTML: {e}")
        return []
    
    # Extract data with validation
    links = []
    for link in soup.select(".StyledPropertyCardDataWrapper a"):
        href = link.get("href")
        if validate_link(href):
            links.append(href)
    
    addresses = []
    for node in soup.select(".StyledPropertyCardDataWrapper address"):
        addr = validate_address(node.get_text())
        if addr:
            addresses.append(addr)
    
    prices = []
    for node in soup.select(".PropertyCardWrapper span"):
        if "$" in node.get_text():
            price_value = validate_price(node.get_text())
            if price_value >= 0:
                prices.append(node.get_text())
    
    logger.info(f"Extracted {len(addresses)} addresses, {len(prices)} prices, {len(links)} links")
    
    # Combine data
    items: list[dict] = []
    for address, price_text, link in zip(addresses, prices, links, strict=False):
        price_value = validate_price(price_text)
        
        item = {
            "address": address,
            "price_text": price_text,
            "price_value": price_value,
            "link": link,
        }
        items.append(item)
        logger.debug(f"Parsed property: {address} - ${price_value:.2f}")
    
    logger.info(f"Successfully parsed {len(items)} properties")
    return items

