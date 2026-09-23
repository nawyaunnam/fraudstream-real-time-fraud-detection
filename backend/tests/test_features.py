from app.features import haversine_km


def test_haversine_known_distance():
    distance = haversine_km(40.7128, -74.0060, 51.5074, -0.1278)
    assert 5500 < distance < 5650

