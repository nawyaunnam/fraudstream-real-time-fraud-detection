from app.schemas import Features
from app.scoring import combine, rule_score


def features(**changes):
    values = dict(amount=100, velocity_1m=0, velocity_1h=2, amount_zscore=0, distance_from_last_km=2, seconds_since_last=900, new_device=0, country_changed=0, card_present=1)
    values.update(changes)
    return Features(**values)


def test_normal_transaction_has_no_rule_score():
    assert rule_score(features()) == (0, [])


def test_velocity_and_unusual_amount_are_additive():
    score, reasons = rule_score(features(velocity_1m=5, amount_zscore=4))
    assert score == 0.65
    assert reasons == ["high_velocity", "unusual_amount"]


def test_impossible_travel_requires_short_time_window():
    assert "impossible_travel" in rule_score(features(distance_from_last_km=1000, seconds_since_last=300))[1]
    assert "impossible_travel" not in rule_score(features(distance_from_last_km=1000, seconds_since_last=10000))[1]


def test_combination_weights_model_more_heavily():
    assert combine(1.0, 0.0) == 0.4
    assert combine(0.0, 1.0) == 0.6

