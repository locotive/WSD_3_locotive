import pytest
from app import create_app
from app.database import get_db, init_db

@pytest.fixture
def client():
    """테스트 클라이언트 설정"""
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

def test_register_user(client):
    """회원가입 API 테스트"""
    response = client.post('/auth/register', json={
        "email": "test@example.com",
        "password": "test123!@#",
        "name": "테스트",
        "phone": "010-1234-5678"
    })
    
    assert response.status_code == 200
    assert "access_token" in response.json

def test_login(client):
    """로그인 API 테스트"""
    # 회원가입
    client.post('/auth/register', json={
        "email": "test@example.com",
        "password": "test123!@#",
        "name": "테스트"
    })
    
    # 로그인
    response = client.post('/auth/login', json={
        "email": "test@example.com",
        "password": "test123!@#"
    })
    
    assert response.status_code == 200
    assert "access_token" in response.json

def test_job_list(client):
    """채용공고 목록 API 테스트"""
    response = client.get('/jobs')
    assert response.status_code == 200
    assert "jobs" in response.json
    assert "pagination" in response.json

def test_job_search(client):
    """채용공고 검색 API 테스트"""
    response = client.get('/jobs?keyword=python&location_id=1')
    assert response.status_code == 200
    
    jobs = response.json["jobs"]
    assert isinstance(jobs, list)
    assert all("python" in job["title"].lower() for job in jobs)

def test_apply_job(client):
    """채용공고 지원 API 테스트"""
    # 로그인
    login_response = client.post('/auth/login', json={
        "email": "test@example.com",
        "password": "test123!@#"
    })
    token = login_response.json["access_token"]
    
    # 지원
    response = client.post(
        '/applications',
        json={"posting_id": 1},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200

def test_rate_limit(client):
    """Rate Limiting 테스트"""
    for _ in range(101):  # 기본 제한: 100req/min
        response = client.get('/jobs')
    
    assert response.status_code == 429 