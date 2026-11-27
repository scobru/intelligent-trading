import dashboard


def test_public_host(monkeypatch):
    monkeypatch.delenv("PUBLIC_HOST", raising=False)
    dashboard._public_host.cache_clear()
    assert dashboard._public_host("203.0.113.5") == "203.0.113.5"
    assert dashboard._public_host("localhost") == "127.0.0.1"
    assert dashboard._public_host("no-such-host.invalid") == "no-such-host.invalid"
    monkeypatch.setenv("PUBLIC_HOST", "1.2.3.4")
    dashboard._public_host.cache_clear()
    assert dashboard._public_host("intelligent-trading-live.example.dev") == "1.2.3.4"
    dashboard._public_host.cache_clear()
