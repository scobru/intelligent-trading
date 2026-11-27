import pytest

import run


def test_parse_strategies():
    assert run.parse_strategies(" DCA, lp,dca ") == ["dca", "lp"]
    with pytest.raises(SystemExit):
        run.parse_strategies("")
    with pytest.raises(SystemExit):
        run.parse_strategies("dca,moon")


def test_build_env_isolates_wallets_and_state():
    base = {
        "PRIVATE_KEY": "shared", "SQLITE_DB_PATH": "/x.db", "OPENROUTER_API_KEY": "k",
        "AGENT_DCA_PRIVATE_KEY": "dca-key", "AGENT_LP_PRIVATE_KEY": "lp-key",
        "AGENT_DCA_TRADING_INTERVAL": "60", "MASTER_PRIVATE_KEY": "master",
        "TELEGRAM_BOT_TOKEN": "t", "AGENT_LP_TELEGRAM_BOT_TOKEN": "lp-t",
    }
    dca = run.build_env("dca", base, ["coordinator", "dca", "lp"])
    assert dca["PRIVATE_KEY"] == "dca-key"
    assert dca["TRADING_INTERVAL"] == "60"
    assert dca["OPENROUTER_API_KEY"] == "k"
    assert "SQLITE_DB_PATH" not in dca
    assert not any(k.startswith("AGENT_") for k in dca)
    assert "MASTER_PRIVATE_KEY" not in dca
    assert dca["PORT"] == "3005" and dca["TELEGRAM_LISTENER"] == "false"

    lp = run.build_env("lp", base, ["coordinator", "dca", "lp"])
    assert lp["PRIVATE_KEY"] == "lp-key" and lp["TELEGRAM_BOT_TOKEN"] == "lp-t"
    assert lp["TELEGRAM_LISTENER"] == "true"

    # a strategy without its own key gets none, never the shared one
    assert "PRIVATE_KEY" not in run.build_env("yield", base, ["yield"])

    coord = run.build_env("coordinator", base, ["coordinator", "dca", "lp"])
    assert coord["AGENT_DCA_URL"] == "http://localhost:3005"
    assert coord["AGENT_LP_PRIVATE_KEY"] == "lp-key"
    assert coord["MASTER_PRIVATE_KEY"] == "master"
    assert coord["SQLITE_DB_PATH"].endswith("agents/coordinator/data/coordinator.db")


def test_synfutures_ports_do_not_collide():
    perp = run.build_env("perp", {}, ["perp", "neutral"])
    neutral = run.build_env("neutral", {}, ["perp", "neutral"])
    assert perp["SYNFUTURES_PORT"] != neutral["SYNFUTURES_PORT"]
    assert neutral["SYNFUTURES_SERVICE_URL"].endswith(neutral["SYNFUTURES_PORT"])


def test_missing_settings():
    assert run.missing_settings("coordinator", {}) == []
    assert len(run.missing_settings("yield", {})) == 2
    assert run.missing_settings("dca", {"WALLET_ADDRESS": "0x1", "OPENROUTER_API_KEY": "k"}) == []


def test_coordinator_wallet_becomes_agent_wallet_address():
    base = {"AGENT_DEGEN_WALLET": "0xabc", "AGENT_YIELD_WALLET": "0xdef", "AGENT_YIELD_WALLET_ADDRESS": "0x123"}
    assert run.build_env("degen", base, ["degen"])["WALLET_ADDRESS"] == "0xabc"
    assert run.build_env("yield", base, ["yield"])["WALLET_ADDRESS"] == "0x123"  # explicit wins
    assert "WALLET_ADDRESS" not in run.build_env("coordinator", base, ["coordinator"])


def test_coordinator_first_cycle_delay_default_and_override():
    assert run.build_env("coordinator", {}, ["coordinator"])["COORDINATOR_START_DELAY"] == "180"
    assert run.build_env("coordinator", {"COORDINATOR_START_DELAY": "5"}, ["coordinator"])["COORDINATOR_START_DELAY"] == "5"
