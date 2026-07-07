from fastapi.testclient import TestClient
from app import app
from knowledge_base import get_rag_context

client = TestClient(app)


def test_health_endpoint():
    response = client.get('/api/health')
    assert response.status_code == 200


def test_chat_fallback_hindi():
    response = client.post('/api/chat', json={'message': 'गेहूं की खेती कैसे करें?', 'language': 'hi'})
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'गेहूं' in data['response'] or 'गेहूं' in data['response']


def test_chat_fallback_english():
    response = client.post('/api/chat', json={'message': 'How to improve soil health?', 'language': 'en'})
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True


def test_rag_context_contains_knowledge_base_facts():
    context = get_rag_context('How to grow wheat?')
    assert 'wheat' in context.lower() or 'गेहूं' in context.lower()
    assert 'sowing time' in context.lower() or 'drainage' in context.lower()


def test_price_predict_endpoint():
    response = client.post('/api/price-predict', json={'crop': 'wheat', 'region': 'punjab'})
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'predicted_price' in data


def test_image_analysis_endpoint():
    response = client.post(
        '/api/analyze-image',
        files={'file': ('leaf.png', b'fake-image-data', 'image/png')},
        data={'message': 'Leaf looks yellow'}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'advice' in data


def test_compare_models_endpoint():
    response = client.post('/api/compare-models', json={'message': 'How to improve soil health?', 'language': 'en'})
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert len(data['comparisons']) >= 2


def test_pest_treatment_endpoint():
    response = client.post('/api/pest-treatment', json={'message': 'There is aphid attack on wheat leaves', 'language': 'en'})
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'advice' in data


def test_weather_endpoint():
    response = client.get('/api/weather')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'today' in data['data']


def test_schemes_endpoint():
    response = client.get('/api/schemes')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert len(data['schemes']) >= 1


def test_dashboard_endpoint():
    response = client.get('/api/dashboard')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'tip' in data['data']


def test_crop_calendar_endpoint():
    response = client.get('/api/crop-calendar?season=rabi&state=punjab')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert len(data['crops']) >= 1


def test_offline_mode_endpoint():
    response = client.get('/api/offline-mode')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'tips' in data


def test_soil_health_checker_endpoint():
    response = client.post('/api/soil-health-check', json={
        'soil_type': 'clay',
        'symptoms': 'yellow leaves, poor growth'
    })
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'fertilizer' in data['recommendations']
    assert data['health_score'] >= 0
