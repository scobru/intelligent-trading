import importlib

import config


def test_strategies_env_filters_agents_and_weights(monkeypatch):
    monkeypatch.setenv("STRATEGIES", "coordinator,dca,lp")
    monkeypatch.setenv("AGENT_DCA_PUBLIC_URL", "http://h:3005")
    try:
        c = importlib.reload(config)
        assert set(c.AGENTS) == {"dca", "lp"}
        for weights in c.REGIME_TARGET_WEIGHTS.values():
            assert set(weights) <= {"dca", "lp"}
            assert abs(sum(weights.values()) - 1.0) < 0.001
        assert c.AGENTS["dca"]["public_url"] == "http://h:3005"
        assert c.AGENTS["lp"]["public_url"] == ""
    finally:
        monkeypatch.delenv("STRATEGIES")
        importlib.reload(config)
