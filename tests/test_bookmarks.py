def test_toggle_bookmark(client, auth_headers):
    # 북마크 추가
    response = client.post('/bookmarks', 
        json={'posting_id': 1},
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # 북마크 제거 (토글)
    response = client.post('/bookmarks', 
        json={'posting_id': 1},
        headers=auth_headers
    )
    assert response.status_code == 200

def test_list_bookmarks(client, auth_headers):
    response = client.get('/bookmarks', headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json, list) 