from app.core.security import generate_api_key, hash_api_key


def test_generate_api_key_has_prefix_and_entropy():
    key = generate_api_key()
    assert key.startswith("mk_")
    assert len(key) > 20


def test_hash_api_key_is_deterministic():
    assert hash_api_key("abc") == hash_api_key("abc")
    assert hash_api_key("abc") != hash_api_key("abcd")
