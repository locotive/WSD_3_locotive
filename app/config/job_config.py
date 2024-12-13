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