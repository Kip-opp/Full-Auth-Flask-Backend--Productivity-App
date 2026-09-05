"""Tests for the public read-only demo workspace."""


def test_demo_workspace_is_public_and_curated(client):
    response = client.get('/api/demo/workspace')

    assert response.status_code == 200
    data = response.get_json()['data']
    assert data['workspace']['id'] == 'demo'
    assert data['workspace']['name'] == 'Notebook demo'
    assert data['sources']
    assert data['notes']
    assert data['artifacts']
    assert all('user_id' not in item for item in data['sources'])


def test_demo_workspace_does_not_make_private_routes_public(client):
    response = client.get('/api/v1/workspaces')

    assert response.status_code == 401