import logging
import random
import time
from contextlib import contextmanager

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ScraperClient:
    """HTTP client for web scraping with retry logic and timeouts."""
    
    def __init__(self) -> None:
        self.session = requests.Session()
        self._configure_session()
    
    def _configure_session(self) -> None:
        """Configure session with retry strategy."""
        # Setup retry strategy for network errors
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _build_headers(self) -> dict[str, str]:
        """Build request headers with random user agent."""
        return {
            "User-Agent": random.choice(settings.user_agents),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def _choose_proxy(self) -> dict[str, str] | None:
        """Choose random proxy from configured list."""
        if not settings.proxies:
            return None
        proxy = random.choice(settings.proxies)
        return {"http": proxy, "https": proxy}

    @contextmanager
    def _request_context(self, url: str):
        """Context manager for request handling."""
        logger.debug(f"Starting request to {url}")
        start_time = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            logger.debug(f"Request to {url} completed in {elapsed:.2f}s")

    def get(self, url: str) -> str:
        """
        Get URL content with retries and exponential backoff.
        
        Args:
            url: URL to fetch
            
        Returns:
            Response text content
            
        Raises:
            requests.RequestException: If all retries fail
        """
        if not url or not isinstance(url, str):
            raise ValueError(f"Invalid URL: {url}")

        for attempt in range(settings.max_retries + 1):
            try:
                with self._request_context(url):
                    response = self.session.get(
                        url,
                        headers=self._build_headers(),
                        proxies=self._choose_proxy(),
                        timeout=(5, settings.request_timeout),  # (connect, read) timeouts
                        allow_redirects=True,
                    )
                    response.raise_for_status()
                    
                    if not response.text:
                        raise ValueError("Empty response received")
                    
                    logger.info(f"✓ Successfully retrieved {url} ({len(response.text)} bytes)")
                    return response.text
                    
            except requests.Timeout as exc:
                logger.warning(
                    f"Request timeout for {url} (attempt {attempt + 1}/{settings.max_retries + 1})"
                )
                if attempt >= settings.max_retries:
                    logger.error(f"✗ Request timeout after {settings.max_retries} retries: {url}")
                    raise exc
                    
            except requests.ConnectionError as exc:
                logger.warning(
                    f"Connection error for {url} (attempt {attempt + 1}/{settings.max_retries + 1})"
                )
                if attempt >= settings.max_retries:
                    logger.error(f"✗ Connection error after {settings.max_retries} retries: {url}")
                    raise exc
                    
            except requests.HTTPError as exc:
                logger.warning(
                    f"HTTP error {exc.response.status_code} for {url} "
                    f"(attempt {attempt + 1}/{settings.max_retries + 1})"
                )
                if exc.response.status_code == 429:
                    # Rate limited - use longer backoff
                    backoff = settings.retry_delay_seconds * (settings.retry_backoff_seconds ** (attempt + 2))
                else:
                    backoff = settings.retry_backoff_seconds * (2 ** attempt)
                    
                if attempt >= settings.max_retries:
                    logger.error(f"✗ HTTP error after {settings.max_retries} retries: {url}")
                    raise exc
                    
            except requests.RequestException as exc:
                logger.warning(
                    f"Request failed for {url} (attempt {attempt + 1}/{settings.max_retries + 1}): {exc}"
                )
                if attempt >= settings.max_retries:
                    logger.error(f"✗ Request failed after {settings.max_retries} retries: {url}")
                    raise exc
            
            # Exponential backoff with jitter
            backoff = settings.retry_backoff_seconds * (2 ** attempt)
            jitter = random.uniform(0, 0.5)
            sleep_for = backoff + jitter
            logger.info(f"Retrying in {sleep_for:.2f}s...")
            time.sleep(sleep_for)
        
        raise RuntimeError("Unreachable retry loop")
    
    def close(self) -> None:
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

