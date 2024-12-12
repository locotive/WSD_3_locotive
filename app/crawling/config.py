from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CrawlingConfig:
    BASE_URL: str = "https://www.saramin.co.kr"
    SEARCH_URL: str = f"{BASE_URL}/zf_user/jobs/list/job-category"
    DETAIL_URL: str = f"{BASE_URL}/zf_user/jobs/relay/view"
    
    # 수집할 페이지 수
    MAX_PAGES: int = 50  # 한 페이지당 20개, 총 1000개
    
    # 재시도 설정
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5  # seconds
    
    # 요청 헤더
    HEADERS: dict = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    } 