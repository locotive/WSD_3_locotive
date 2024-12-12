def test_list_jobs(client):
    response = client.get('/jobs')
    assert response.status_code == 200
    assert 'jobs' in response.json
    
def test_search_jobs(client):
    response = client.get('/jobs?keyword=python')
    assert response.status_code == 200
    assert 'jobs' in response.json

def test_job_detail(client):
    # 먼저 job_id 1이 있다고 가정
    response = client.get('/jobs/1')
    assert response.status_code == 200
    assert 'job' in response.json

def test_job_filters(client):
    # 여러 필터 조건으로 테스트
    response = client.get('/jobs?location_id=1&experience_level=신입')
    assert response.status_code == 200
    
    response = client.get('/jobs?tech_stacks=Python,Java')
    assert response.status_code == 200 