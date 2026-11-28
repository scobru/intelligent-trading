from risk_engine import RiskEngine


def test_perp_side_size_counts_and_paper_scale_applies():
    agents = {
        "perp": {"equity_usd": 700.0, "paper_scale": 0.07,
                 "positions": [{"side": "long", "size": 10.0, "mark_price": 1000.0}]},
        "dca": {"equity_usd": 2500.0, "paper_scale": 0.25,
                "raw": {"portfolio": {"assets": {"USDC": {"value_usd": 3000}, "CBBTC": {"value_usd": 7000}}}}},
    }
    r = RiskEngine().evaluate_portfolio_risk(agents)
    # perp: 10 x 1000 notional x 0.07 = 700 long; dca: 7000 crypto x 0.25 = 1750 long
    assert r["net_delta_usd"] == 2450.0
