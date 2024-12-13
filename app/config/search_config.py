from .location_config import LocationConfig
from .job_config import JobConfig

class SearchConfig:
    def __init__(self):
        self._sort_options = {
            "최신순": "latest",
            "관련도순": "relevance",
            "마감임박순": "deadline",
            "경력순": "experience"
        }
        
        self._filters = {
            "경력": {
                "신입": "1",
                "경력": "2",
                "무관": "0"
            },
            "고용형태": {
                "정규직": "1",
                "계약직": "2",
                "인턴": "3"
            }
        }
    
    def get_sort_code(self, sort_type):
        return self._sort_options.get(sort_type)
    
    def get_filter_code(self, filter_type, value):
        return self._filters.get(filter_type, {}).get(value)

class SearchParams:
    def __init__(self):
        self.location = LocationConfig()
        self.job = JobConfig()
        self.search = SearchConfig()
    
    def build_params(self, **kwargs):
        """검색 파라미터 생성"""
        params = {
            "searchType": "search",
            "searchword": kwargs.get("keyword", ""),
            "recruitPage": kwargs.get("page", 1)
        }
        
        # 지역 코드 추가
        if region := kwargs.get("region"):
            if code := self.location.get_code(region):
                params["loc_cd"] = code
                
        # 직무 코드 추가
        if job := kwargs.get("job"):
            if code := self.job.get_code(job):
                params["job_cd"] = code
                
        # 정렬 옵션 추가
        if sort := kwargs.get("sort"):
            if code := self.search.get_sort_code(sort):
                params["sort"] = code
                
        # 필터 추가
        if exp := kwargs.get("experience"):
            if code := self.search.get_filter_code("경력", exp):
                params["exp_cd"] = code
                
        if emp := kwargs.get("employment"):
            if code := self.search.get_filter_code("고용형태", emp):
                params["emp_cd"] = code
        
        return params 