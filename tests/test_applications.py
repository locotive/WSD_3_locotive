def test_apply_job(client, auth_headers):
    response = client.post('/applications', 
        json={'posting_id': 1},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert 'application_id' in response.json

def test_list_applications(client, auth_headers):
    response = client.get('/applications', headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_cancel_application(client, auth_headers):
    # 먼저 지원하기
    apply_response = client.post('/applications', 
        json={'posting_id': 1},
        headers=auth_headers
    )
    
    # 지원 취소
    application_id = apply_response.json['application_id']
    response = client.delete(f'/applications/{application_id}', 
        headers=auth_headers
    )
    assert response.status_code == 200 