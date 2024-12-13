class LocationConfig:
    def __init__(self):
        self._codes = {
            "수도권": {"서울": "101000", "경기": "102000", "인천": "108000"},
            "광역시": {"부산": "106000", "대구": "104000", "광주": "103000", 
                    "대전": "105000", "울산": "107000", "세종": "118000"},
            "도": {"강원": "109000", "경남": "110000", "경북": "111000",
                 "전남": "112000", "전북": "113000", "충남": "115000", 
                 "충북": "114000", "제주": "116000"},
            "해외": {"아시아": "210000", "북미": "220000", "유럽": "240000", 
                   "오세아니아": "250000"}
        }
        
    def get_code(self, region, sub_region=None):
        if sub_region:
            return self._codes.get(region, {}).get(sub_region)
        return next((code for r in self._codes.values() 
                    for loc, code in r.items() if loc == region), None)

class JobConfig:
    def __init__(self):
        self._categories = {
            "개발": {
                "백엔드": "2001",
                "프론트엔드": "2002",
                "풀스택": "2003",
                "모바일": "2004",
                "데이터": "2005",
                "DevOps": "2006"
            },
            "기획": {
                "서비스기획": "1601",
                "프로젝트관리": "1602",
                "전략기획": "1603"
            },
            "디자인": {
                "UX/UI": "1501",
                "웹디자인": "1502",
                "그래픽": "1503"
            }
        }
    
    def get_code(self, category, sub_category=None):
        if sub_category:
            return self._categories.get(category, {}).get(sub_category)
        return next((code for cat in self._categories.values() 
                    for job, code in cat.items() if job == category), None)

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