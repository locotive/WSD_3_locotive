from dataclasses import dataclass, field
from typing import Dict

@dataclass
class CrawlingConfig:
    BASE_URL: str = "https://www.saramin.co.kr"
    SEARCH_URL: str = field(init=False)
    DETAIL_URL: str = field(init=False)
    MAX_PAGES: int = 5
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5
    HEADERS: Dict = field(default_factory=lambda: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    def __post_init__(self):
        self.SEARCH_URL = f"{self.BASE_URL}/zf_user/search/recruit"
        self.DETAIL_URL = f"{self.BASE_URL}/zf_user/jobs/relay/view"