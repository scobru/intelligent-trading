import json

import config
from agent_client import AgentClient
from treasury import Treasury


def _ledger(treasury_usdc, allocs):
    with open(config.PAPER_ACCOUNT_FILE, "w", encoding="utf-8") as fh:
        json.dump({"treasury_usdc": treasury_usdc, "virtual_allocations": allocs}, fh)


def _read():
    with open(config.PAPER_ACCOUNT_FILE, encoding="utf-8") as fh:
        return json.load(fh)


def test_paper_transfer_moves_only_what_sender_has(monkeypatch):
    monkeypatch.setattr(config, "PAPER_TRADING", True)
    _ledger(100.0, {"lp": 1500.0, "degen": 300.0})
    t = Treasury()
    status = {"degen": {"wallet": "0x1"}, "lp": {"wallet": "0x2"}}
    # allocator asks for more than lp holds: before the fix degen got +10600 out of nothing
    t.execute_rebalance_action({"action": "X", "from_agent": "lp", "to_agent": "degen", "amount_usd": 10600.0}, status)
    st = _read()
    assert st["virtual_allocations"] == {"lp": 0.0, "degen": 1800.0}
    t.execute_rebalance_action({"action": "X", "from_agent": "master_treasury", "to_agent": "lp", "amount_usd": 500.0}, status)
    st = _read()
    assert st["treasury_usdc"] == 0.0 and st["virtual_allocations"]["lp"] == 100.0
    total = st["treasury_usdc"] + sum(st["virtual_allocations"].values())
    assert total == 1900.0  # conserved


def test_agent_equity_is_its_allocation_times_paper_return(monkeypatch):
    monkeypatch.setattr(config, "PAPER_TRADING", True)
    _ledger(0.0, {"perp": 700.0})
    res = {"id": "perp", "equity_usd": 11000.0, "balance_usd": 5000.0}
    AgentClient._apply_paper_ledger(res, {"initial_usdc": 10000.0})
    assert res["equity_usd"] == 770.0  # +10% on 700
    assert res["balance_usd"] == 350.0
    res = {"id": "degen", "equity_usd": 10000.0, "balance_usd": 10000.0}
    AgentClient._apply_paper_ledger(res, {"initial_usdc": 10000.0})
    assert res["equity_usd"] == 0.0  # not funded by the coordinator


def test_live_mode_is_untouched(monkeypatch):
    monkeypatch.setattr(config, "PAPER_TRADING", False)
    _ledger(0.0, {"perp": 700.0})
    res = {"id": "perp", "equity_usd": 11000.0, "balance_usd": 5000.0}
    AgentClient._apply_paper_ledger(res, {"initial_usdc": 10000.0})
    assert res["equity_usd"] == 11000.0


def test_initial_ledger_splits_starting_capital(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "PAPER_TRADING", True)
    monkeypatch.setattr(config, "PAPER_START_USDC", 10000.0)
    monkeypatch.setattr(config, "AGENTS", {"lp": {}, "degen": {}})
    Treasury()
    st = _read()
    assert st["virtual_allocations"] == {"lp": 1500.0, "degen": 300.0}
    assert st["treasury_usdc"] + sum(st["virtual_allocations"].values()) == 10000.0
