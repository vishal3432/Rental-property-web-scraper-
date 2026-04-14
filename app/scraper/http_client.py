import logging
import random
import time

import requests

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ScraperClient:
    def __init__(self) -> None:
        self.session = requests.Session()

    def _build_headers(self) -> dict[str, str]:
        return {
            "User-Agent": random.choice(settings.user_agents),
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _choose_proxy(self) -> dict[str, str] | None:
        if not settings.proxies:
            return None
        proxy = random.choice(settings.proxies)
        return {"http": proxy, "https": proxy}

    def get(self, url: str) -> str:
        for attempt in range(settings.max_retries + 1):
            try:
                response = self.session.get(
                    url,
                    headers=self._build_headers(),
                    proxies=self._choose_proxy(),
                    timeout=settings.request_timeout,
                )
                response.raise_for_status()
                return response.text
            except requests.RequestException as exc:
                if attempt >= settings.max_retries:
                    logger.exception("Request failed after retries")
                    raise exc
                backoff = settings.retry_backoff_seconds * (2**attempt)
                jitter = random.uniform(0, 0.25)
                sleep_for = backoff + jitter
                logger.warning("Request failed, retrying in %.2fs (%s)", sleep_for, exc)
                time.sleep(sleep_for)
        raise RuntimeError("Unreachable retry loop")
