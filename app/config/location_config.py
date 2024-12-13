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