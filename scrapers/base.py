from __future__ import annotations

from abc import ABC, abstractmethod
from urllib.parse import quote_plus

from utils.logging import LogCallback
from utils.models import Lead


class BaseScraper(ABC):
    source_name = "Base"

    def __init__(self, category: str, location: str, limit: int, log: LogCallback | None = None):
        self.category = category
        self.location = location
        self.limit = max(1, int(limit))
        self.log = log

    @property
    def query(self) -> str:
        return f"{self.category} in {self.location}"

    @property
    def query_encoded(self) -> str:
        return quote_plus(self.query)

    @abstractmethod
    async def scrape(self, context) -> list[Lead]:
        raise NotImplementedError
