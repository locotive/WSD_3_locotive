import pytest
from app.jobs.models import Job
from app.jobs.schemas import JobSchema

def test_job_schema_validation():
    """채용공고 스키마 검증 테스트"""
    valid_data = {
        "title": "Python 개발자",
        "company_id": 1,
        "location_id": 1,
        "experience_level": "신입",
        "education_level": "학사",
        "job_description": "Python 개발자 구합니다",
        "tech_stacks": ["Python", "Flask", "MySQL"]
    }
    
    schema = JobSchema()
    result = schema.load(valid_data)
    assert result["title"] == valid_data["title"]
    
    # 필수 필드 누락 테스트
    invalid_data = {
        "title": "Python 개발자"
    }
    
    with pytest.raises(Exception):
        schema.load(invalid_data)

def test_job_search():
    """채용공고 검색 테스트"""
    filters = {
        "keyword": "python",
        "location_id": 1,
        "tech_stacks": ["Python", "Flask"]
    }
    
    jobs = Job.search(filters)
    assert isinstance(jobs, list)
    assert all("python" in job["title"].lower() for job in jobs) 