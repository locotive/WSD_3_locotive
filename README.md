# Job Search API

채용정보 검색 및 지원 API 서비스

## 주요 기능

### 크롤링
- 사람인 채용정보 자동 수집
- 비동기 크롤링으로 성능 최적화
- 스케줄링된 자동 업데이트

### 사용자 기능
- JWT 기반 회원 인증
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
- Selenium (필요시)

### 모니터링
- Prometheus
- APScheduler
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

1. 개발 서버 실행
```bash
flask run --host=0.0.0.0 --port=17102
```

2. 크롤링 스케줄러 실행
```bash
python -m app.crawling.scheduler
```

## 프로젝트 구조
```
job-search-api/
├── app/
│   ├── __init__.py          # 앱 초기화 및 설정
│   ├── auth/               # 인증 관련
│   ├── jobs/              # 채용정보 관련
│   ├── crawling/          # 크롤링 관련
│   ├── middleware/        # 미들웨어
│   ├── common/           # 공통 유틸리티
│   └── docs/             # API 문서
├── tests/
│   ├── unit/            # 단위 테스트
│   └── integration/     # 통합 테스트
├── migrations/          # DB 마이그레이션
├── static/
│   └── swagger.json    # Swagger 문서
├── logs/               # 로그 파일
├── requirements.txt    # 의존성 목록
└── README.md
```

## API 문서

Swagger UI: http://113.198.66.75:17102/api/docs

### 주요 엔드포인트

#### 인증
- `POST /auth/register`: 회원가입
- `POST /auth/login`: 로그인
- `POST /auth/refresh`: 토큰 갱신

#### 채용정보
- `GET /jobs`: 채용공고 목록
- `GET /jobs/search`: 채용공고 검색
- `GET /jobs/{id}`: 채용공고 상세

#### 지원
- `POST /applications`: 채용공고 지원
- `GET /applications`: 지원 내역 조회
- `GET /applications/{id}`: 지원 상세

#### 북마크
- `POST /bookmarks`: 북마크 추가
- `GET /bookmarks`: 북마크 목록
- `DELETE /bookmarks/{id}`: 북마크 삭제

## 포트 구성
- SSH: 19102
- Backend(Flask): 17102
- Database(MySQL): 13102

## 모니터링

### Prometheus 메트릭
- 엔드포인트: http://113.198.66.75:17102/metrics
- 주요 메트릭:
  - 요청 수
  - 응답 시간
  - 에러율
  - 크롤링 성공/실패

### 로깅
- 위치: `logs/`
- 로그 레벨: INFO, ERROR
- 로그 포맷: JSON

## 테스트

```bash
# 전체 테스트 실행
pytest

# 커버리지 리포트 생성
pytest --cov=app tests/
```

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