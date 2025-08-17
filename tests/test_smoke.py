from aitc.converter import drop_empty, to_number

def test_drop_empty():
    d = {"a": None, "b": "", "c": "ok", "d": ["", None, "x"]}
    out = drop_empty(d)
    assert out == {"c": "ok", "d": ["x"]}

def test_to_number():
    assert to_number("$1,234.50") == 1234.5
    assert to_number("") is None
