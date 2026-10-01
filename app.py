def add(a: float, b: float) -> float:
    """Palauta kahden luvun summa."""
    return a + b


def classify_temperature(celsius: float) -> str:
    """Luokittele lämpötila yksinkertaisesti."""
    if celsius < 0:
        return "freezing"
    if celsius < 20:
        return "cool"
    return "warm"


if __name__ == "__main__":
    print(classify_temperature(21))
