# 채용 플랫폼 API

## 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [기술 스택](#기술-스택)
3. [설치 및 실행 방법](#설치-및-실행-방법)
4. [환경 설정](#환경-설정)
5. [API 문서](#api-문서)
6. [데이터베이스](#데이터베이스)
7. [크롤링](#크롤링)
8. [Reference](#reference)

## 프로젝트 개요
사람인 채용정보를 크롤링하여 제공하는 채용 플랫폼 API 서비스입니다.

### 주요 기능
- 채용공고 검색 및 필터링
- 이력서 관리
- 채용공고 지원
- 북마크 기능

### 검색 및 필터링
- 키워드 검색
- 기술 스택 필터
- 지역 필터
- 경력 필터

## 기술 스택

### Backend
- Python 3.8+
- Flask 2.0.1
- MySQL 8.0+
- Redis 4.0+

### 크롤링
- aiohttp
- BeautifulSoup4
- Selenium
- APScheduler

### 모니터링
- Prometheus
- Logging

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/yourusername/job-search-api.git
cd job-search-api
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 환경변수 설정
```bash
cp .env.example .env
```

필수 환경변수:
- `DB_HOST`: 데이터베이스 호스트
- `DB_USER`: 데이터베이스 사용자
- `DB_PASSWORD`: 데이터베이스 비밀번호
- `DB_NAME`: 데이터베이스 이름
- `JWT_SECRET_KEY`: JWT 시크릿 키
- `REDIS_URL`: Redis 연결 URL

5. 데이터베이스 마이그레이션
```bash
flask db upgrade
```

## 실행 방법

### 로컬 개발 환경
1. Flask 개발 서버 실행
```bash
flask run  # http://localhost:5000
```

2. API 문서 접속
```
http://localhost:5000/api/docs
http://113.198.66.75:17102/api/docs
```

3. 크롤링 테스트
- Swagger UI에서 테스트: http://localhost:5000/api/docs
- 직접 API 호출:
  - 수동 크롤링: POST http://localhost:5000/crawling/manual
  - 크롤링 상태: GET http://localhost:5000/crawling/status
  - 크롤링 로그: GET http://localhost:5000/crawling/logs

### 서버 환경
1. 서버 실행
```bash
flask run --host=0.0.0.0 --port=17102
```

2. API 문서
```
http://113.198.66.75:17102/api/docs
```

## API 문서

Swagger UI: http://113.198.66.75:17102/api/docs

## API 엔드포인트

### Authentication (인증)
- `POST /auth/register`: 회원 가입
- `POST /auth/login`: 로그인
- `GET /auth/profile`: 회원 정보 조회
- `PUT /auth/profile`: 회원 정보 수정
- `DELETE /auth/profile`: 회원 탈퇴

### Jobs (채용공고)
- `GET /jobs`: 채용공고 목록 조회
- `POST /jobs`: 채용공고 등록
- `GET /jobs/{posting_id}`: 채용공고 상세 조회
- `PUT /jobs/{posting_id}`: 채용공고 수정
- `DELETE /jobs/{posting_id}`: 채용공고 삭제

### Applications (지원)
- `POST /applications`: 채용공고 지원
- `GET /applications`: 지원 내역 조회
- `DELETE /applications/{application_id}`: 지원 취소

### Bookmarks (북마크)
- `GET /bookmarks/check/{posting_id}`: 북마크 여부 확인
- `POST /bookmarks/add`: 북마크 추가
- `DELETE /bookmarks/remove/{posting_id}`: 북마크 제거
- `GET /bookmarks`: 북마크 목록 조회

### Resumes (이력서)
- `POST /resumes`: 이력서 생성
- `GET /resumes`: 이력서 목록 조회
- `GET /resumes/{resume_id}`: 이력서 상세 조회
- `PUT /resumes/{resume_id}`: 이력서 수정
- `DELETE /resumes/{resume_id}`: 이력서 삭제

### Crawling (크롤링)
- `POST /crawling/manual`: 수동 크롤링 실행
- `GET /crawling/status`: 크롤링 상태 조회
- `GET /crawling/logs`: 크롤링 로그 조회

## 포트 구성
- 로컬 개발: 5000

### 개발 서버
- IP: 113.198.66.75
- 포트 구성:
  - SSH: 19102
  - Backend(Flask): 17102
  - Database(MySQL): 13102
  - Redis: 16102

  ### 접속 정보
- SSH: `ssh -p 19102 ubuntu@113.198.66.75`
- API: `http://113.198.66.75:17102`
- API 문서: `http://113.198.66.75:17102/api/docs`
- Prometheus 메트릭: `http://113.198.66.75:17102/metrics`


## 모니터링

### Prometheus 메트릭
- 로컬: http://localhost:5000/metrics
- 서버: http://113.198.66.75:17102/metrics

주요 메트릭:
- 요청 수
- 응답 시간
- 에러율
- 크롤링 성공/실패

## 성능 최적화
- 데이터베이스 인덱싱
- 캐시 적용 (Redis)
- 페이지네이션 구현

## 라이선스

MIT License

## 기여 방법

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 문의

이슈를 통해 문의해주세요.

## API Reference ID 값

### Location IDs
| ID | 지역 | 코드 |
|----|------|------|
| 1  | 아시아 | 210000 |
| 2  | 북미 | 220000 |
| 3  | 서울 | 101000 |
| 4  | 경기 | 102000 |
| 5  | 인천 | 108000 |
| 6  | 부산 | 106000 |
| 7  | 대구 | 104000 |
| 8  | 광주 | 103000 |
| 9  | 대전 | 105000 |
| 10 | 울산 | 107000 |
| 11 | 세종 | 118000 |
| 12 | 강원 | 109000 |
| 13 | 경남 | 110000 |
| 14 | 경북 | 111000 |
| 15 | 전남 | 112000 |
| 16 | 전북 | 113000 |
| 17 | 충남 | 115000 |
| 18 | 충북 | 114000 |
| 19 | 제주 | 116000 |

### Category IDs
| ID | 카테고리 | 코드 | 상위 카테고리 |
|----|----------|------|--------------|
| 1  | 백엔드 | 2001 | 개발 |
| 2  | 프론트엔드 | 2002 | 개발 |
| 3  | 풀스택 | 2003 | 개발 |
| 4  | 모바일 | 2004 | 개발 |
| 5  | 데이터 | 2005 | 개발 |
| 6  | DevOps | 2006 | 개발 |
| 7  | 서비스기획 | 1601 | 기획 |
| 8  | 프로젝트관리 | 1602 | 기획 |
| 9  | 전략기획 | 1603 | 기획 |
| 10 | UX/UI | 1501 | 디자인 |
| 11 | 웹디자인 | 1502 | 디자인 |
| 12 | 그래픽 | 1503 | 디자인 |

### Tech Stack IDs
| ID | 기술스택 |
|----|----------|
| 1  | Python |
| 2  | JavaScript |
| 3  | Java |
| 4  | React |
| 5  | Node.js |
| 6  | MySQL |
| 7  | AWS |
| 8  | Docker |

## 프로젝트 구조

```
job-search-api/
├── app/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── utils.py
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── utils.py
│   ├── crawling/
│   │   ├── __init__.py
│   │   ├── crawler.py
│   │   └── scheduler.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── job.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── migrations/
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## 데이터베이스 스키마

### users
```sql
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    birth_date DATE,
    status ENUM('active', 'inactive', 'deleted') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### job_postings
```sql
CREATE TABLE job_postings (
    posting_id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT,
    title VARCHAR(255) NOT NULL,
    job_description TEXT NOT NULL,
    experience_level VARCHAR(50),
    education_level VARCHAR(50),
    employment_type VARCHAR(50),
    salary_info VARCHAR(100),
    location_id INT,
    deadline_date DATE,
    view_count INT DEFAULT 0,
    status ENUM('active', 'closed', 'deleted') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id)
);
```

## 크롤링 구현

### 크롤링 프로세스
1. 사람인 API 호출
2. 데이터 파싱 및 전처리
3. 데이터베이스 저장
4. 에러 처리 및 로깅

### 크롤링 코드 예시
```python
from app.crawling.crawler import SaraminCrawler

# 크롤러 초기화
crawler = SaraminCrawler(
    api_key=os.getenv('SARAMIN_API_KEY'),
    db_connection=db.connection
)

# 크롤링 실행
try:
    result = crawler.crawl_jobs()
    print(f"Successfully crawled {result.total_jobs} jobs")
except Exception as e:
    print(f"Crawling failed: {str(e)}")
```

## 에러 처리

### 에러 코드
- 400: 잘못된 요청
- 401: 인증 실패
- 403: 권한 없음
- 404: 리소스 없음
- 409: 충돌 (중복 등)
- 500: 서버 에러

### 에러 응답 예시
```json
{
    "status": "error",
    "message": "Invalid input parameters",
    "errors": [
        {
            "field": "email",
            "message": "Invalid email format"
        }
    ]
}
```

## 보안 설정

### JWT 설정
```python
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
```

### 비밀번호 인코딩
```python
# Base64 인코딩 사용
from base64 import b64encode
password_hash = b64encode(password.encode()).decode()
```

## 모니터링 설정

### Prometheus 설정
```python
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')
```

### 로깅 설정
```python
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
```

## 성능 최적화

### 데이터베이스 인덱스
```sql
-- 채용공고 검색 최적화
CREATE INDEX idx_job_postings_title ON job_postings(title);
CREATE INDEX idx_job_postings_location ON job_postings(location_id);
CREATE INDEX idx_job_postings_status ON job_postings(status);
```

### Redis 캐시
```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.getenv('REDIS_URL')
})

@cache.memoize(timeout=300)
def get_job_posting(posting_id):
    return JobPosting.query.get(posting_id)
```

## 서버 실행 방법

### 백그라운드 서버 실행
```bash
cd /home/ubuntu/WSD_3_locotive/WSD_3_locotive
sudo nohup /home/ubuntu/WSD_3_locotive/venv/bin/python run.py > server.log 2>&1 &
```

### CSV 데이터 DB 저장
```bash
sudo ../venv/bin/python -m app.crawling.utils.csv_to_db
```

### 유용한 명령어
- 프로세스 확인: `ps aux | grep python`
- 서버 로그 확인: `tail -f server.log`
- 프로세스 종료: `kill -9 [프로세스ID]`
```

## 데이터 관리

### 로컬 크롤링 및 데이터 업로드

#### 1. 사전 준비
- Python 3.x 설치
```bash
pip install -r requirements.txt
```

프로젝트 루트에서 로컬 크롤링 실행:
'''bash
python local_crawler.py
'''

#### 2. 환경 설정
1. `.env.example` 파일을 `.env`로 복사:
```bash
cp .env.example .env
```

2. `.env` 파일에서 실제 값으로 수정:
```
DB_HOST=113.198.66.75
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database
DB_PORT=13102
```

> 참고: `.env` 파일은 민감한 정보를 포함하므로 절대 Git에 커밋하지 마세요.

#### 3. 데이터 업로드
로컬에서 크롤링한 CSV 파일을 JCloud DB에 업로드:
```bash
python upload_to_jcloud.py [CSV_FILE_PATH]

# 예시
python upload_to_jcloud.py crawled_data/saramin_jobs_20241215_120320.csv
```

#### 4. 업로드 결과
성공적으로 업로드되면 다음과 같은 메시지가 출력됩니다:
```
CSV 업로드 완료: [N]개 새로 저장, [M]개 업데이트
```

#### 주의사항
- CSV 파일은 크롤링 스크립트에서 자동 생성된 형식을 유지해야 합니다
- 중복된 채용공고는 자동으로 업데이트됩니다
- DB 연결을 위해 올바른 환경변수 설정이 필요합니다
```

## 환경 설정

#### 2. 환경 설정
1. `.env.example` 파일을 `.env`로 복사:
```bash
cp .env.example .env
```

2. `.env` 파일에서 실제 값으로 수정:
```
DB_HOST=113.198.66.75
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database
DB_PORT=13102
```

> 참고: `.env` 파일은 민감한 정보를 포함하므로 절대 Git에 커밋하지 마세요.

## 크롤링

### 크롤링 프로세스
1. 사람인 API 호출
2. 데이터 파싱 및 전처리
3. 데이터베이스 저장
4. 에러 처리 및 로깅

### 크롤링 코드 예시
```python
from app.crawling.crawler import SaraminCrawler
...
```

### 크롤링 시스템

#### 1. 자동 크롤링
매일 새벽 2시에 자동으로 실행되는 크롤링 시스템이 구현되어 있습니다.

```python
@scheduler.task('cron', id='daily_crawling', hour=2)
async def scheduled_crawling():
    with app.app_context():
        try:
            crawler = SaraminCrawler()
            saved_count = await crawler.crawl_jobs()
            app.logger.info(f"자동 크롤링 완료: {saved_count}개 저장")
        except Exception as e:
            app.logger.error(f"자동 크롤링 실패: {str(e)}")
```

#### 2. 수동 크롤링 API
필요한 경우 API를 통해 수동으로 크롤링을 실행할 수 있습니다.

##### 엔드포인트
- 수동 크롤링 실행: `POST /crawling/manual`
- 크롤링 상태 확인: `GET /crawling/status`
- 크롤링 로그 조회: `GET /crawling/logs`

##### API 사용 예시
```bash
# 수동 크롤링 실행
curl -X POST http://113.198.66.75:17102/crawling/manual

# 크롤링 상태 확인
curl http://113.198.66.75:17102/crawling/status

# 크롤링 로그 조회
curl http://113.198.66.75:17102/crawling/logs
```

#### 3. 크롤링 프로세스 상세
1. 데이터 수집
   - 사람인 채용공고 페이지 크롤링
   - aiohttp를 사용한 비동기 요청 처리
   - BeautifulSoup4를 통한 HTML 파싱

2. 데이터 전처리
   - 중복 채용공고 필터링
   - 날짜 형식 변환
   - 필수 필드 유효성 검사

3. 데이터베이스 저장
   - 새로운 채용공고 추가
   - 기존 채용공고 업데이트
   - 트랜잭션 처리

#### 4. 모니터링
- Prometheus 메트릭
  - 크롤링 성공/실패 횟수
  - 처리된 채용공고 수
  - 실행 시간

- 로깅
  - 상세 에러 메시지
  - 처리 단계별 로그
  - 성능 메트릭

#### 5. 에러 처리
- 네트워크 오류 재시도
- 데이터베이스 트랜잭션 롤백
- 알림 시스템 (에러 발생시)

#### 6. 성능 최적화
- 비동기 처리로 동시성 향상
- 배치 처리로 DB 부하 감소
- Redis 캐시로 중복 요청 방지
