# Job Search API

채용정보 검색 및 지원 API 서비스

## 주요 기능

### 크롤링
- 사람인 채용정보 자동 수집
- 비동기 크롤링으로 성능 최적화
- 스케줄링된 자동 업데이트 (매일 새벽 2시)
- 수동 크롤링 API 제공

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
- 서버 환경:
  - SSH: 19102
  - Backend(Flask): 17102
  - Database(MySQL): 13102

## 모니터링

### Prometheus 메트릭
- 로컬: http://localhost:5000/metrics
- 서버: http://113.198.66.75:17102/metrics

주요 메트릭:
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