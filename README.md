# Job Search API

채용정보 검색 및 지원 API 서비스

## 주요 기능

- 사람인 채용정보 크롤링
- 회원 가입/로그인
- 채용공고 검색 및 필터링
- 채용공고 지원
- 북마크 기능

## 기술 스택

- Python 3.8+
- Flask
- MySQL
- Redis
- APScheduler
- Prometheus

## 설치 방법

1. 저장소 클론
bash
git clone https://github.com/yourusername/job-search-api.git
cd job-search-api

2. 가상환경 생성 및 활성화
bash
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

3. 의존성 설치
bash
pip install -r requirements.txt

4. 환경변수 설정
bash
cp .env.example .env
.env 파일 수정

5. 데이터베이스 마이그레이션
bash
python migrations/migrate.py

## 실행 방법

1. 개발 서버 실행
bash
flask run

2. 크롤링 스케줄러 실행
bash
python app/crawling/scheduler.py

## API 문서

- Swagger UI: http://113.198.66.75:17102/api/docs

## 테스트

bash
pytest

## 프로젝트 구조
job-search-api/
├── app/
│ ├── init.py
│ ├── auth/
│ ├── jobs/
│ ├── crawling/
│ ├── middleware/
│ └── common/
├── tests/
│ ├── unit/
│ └── integration/
├── migrations/
├── static/
│ └── swagger.json
├── logs/
├── requirements.txt
└── README.md


## 주요 API 엔드포인트

- `POST /auth/register`: 회원가입
- `POST /auth/login`: 로그인
- `GET /jobs`: 채용공고 목록
- `GET /jobs/search`: 채용공고 검색
- `POST /applications`: 채용공고 지원
- `GET /applications`: 지원 내역 조회

## 모니터링

- Prometheus 메트릭: http://113.198.66.75:17102/metrics

## 포트 구성:
- SSH: 19102
- Backend(Flask): 17102
- Database(MySQL): 13102

## 라이선스

MIT License

## 기여 방법

1. Fork the Project
2. Create your Feature Branch
3. Commit your Changes
4. Push to the Branch
5. Open a Pull Request