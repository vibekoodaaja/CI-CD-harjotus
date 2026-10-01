from app import add, classify_temperature


def test_add() -> None:
    assert add(2, 3) == 6


def test_add_negative_and_float() -> None:
    assert add(-1, 1) == 0
    assert add(0.5, 0.25) == 0.75


def test_temperature_boundaries() -> None:
    assert classify_temperature(-1) == "freezing"
    assert classify_temperature(0) == "cool"
    assert classify_temperature(19.9) == "cool"
    assert classify_temperature(20) == "warm"
