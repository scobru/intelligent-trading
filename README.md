# Intelligent Trading

**AI trading agents built for [Base](https://base.org)**, the Ethereum L2 by Coinbase (chain ID 8453).

[![Built for Base](https://img.shields.io/badge/built%20for-Base-0052FF)](https://base.org)
[![Chain ID 8453](https://img.shields.io/badge/chain%20ID-8453-0052FF)](https://basescan.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> ⚠️ **Experimental software, not financial advice.** These bots trade real money on Base and can lose some or all of the capital you give them. Start with paper trading or dry-run; when you go live, use dedicated wallets and only amounts you can afford to lose. See the **Disclaimer** section at the bottom.

A suite of **autonomous trading agents on [Base](https://base.org)**. Each one
specializes in a single on-chain strategy and is driven by an LLM (through
[OpenRouter](https://openrouter.ai)). A **coordinator** splits capital across
them and watches the overall risk.

Everything is Base-native: contract addresses, protocol integrations, gas
handling and on-chain checks are written for Base mainnet, and every
transaction is signed for chain ID 8453. Every agent
lives in its own repository with its own deployment, and can be used on its
own. The model proposes, the executor decides: every risk limit
is enforced in the executor's code and cannot be bypassed from the prompt.

---

## The suite

| Agent | Strategy | Risk | Protocols on Base |
|---|---|---|---|
| [**perp**](https://github.com/scobru/intelligent-trading-agent-perp) | Directional perpetuals with leverage | High | SynFutures V3 |
| [**degen**](https://github.com/scobru/intelligent-trading-agent-degen) | Speculative spot on new tokens and memecoins | Very high | Uniswap V3, GoPlus security screening |
| [**yield**](https://github.com/scobru/intelligent-trading-agent-yield) | Passive yield on lending markets and vaults, optional looping | Low | Aave V3, Morpho, Moonwell, Compound, ERC-4626 |
| [**neutral**](https://github.com/scobru/intelligent-trading-agent-neutral) | Delta-neutral funding carry (long spot + short perp) | Low-medium | Uniswap V3 + SynFutures V3 |
| [**dca**](https://github.com/scobru/intelligent-trading-agent-dca) | DCA scaled by the Fear & Greed index, plus rebalancing | Medium-low | Uniswap V3 |
| [**lp**](https://github.com/scobru/intelligent-trading-agent-lp) | Concentrated liquidity with range re-centering | Medium | Uniswap V3 |
| [**coordinator**](https://github.com/scobru/intelligent-trading-agent-coordinator) | Control room: market regime, capital allocation, circuit breaker, gas | — | reads and commands the agents through their APIs |

```
                    ┌──────────────────────────────┐
                    │         coordinator          │
                    │  regime · allocation · gas   │
                    │  circuit breaker · dashboard │
                    └──────────────┬───────────────┘
            /api/status · pause · resume · release_funds
   ┌────────┬────────┬─────────────┼────────┬────────┬────────┐
   ▼        ▼        ▼             ▼        ▼        ▼
  perp    degen    yield        neutral    dca       lp
```

## What they share

- **The same decision cycle.** Market data discovery → portfolio state →
  automatic risk exits (before the model is consulted) → LLM decision as
  JSON → executor checks → execution.
- **Three modes.** `PAPER_TRADING` (virtual portfolio with real prices and
  yields), `DRY_RUN` (reads the chain and prints the plan, signs nothing) and
  live. The dashboard always shows which mode is active.
- **Consistent dashboards.** The same design system (`static/dashboard.css`,
  `static/dashboard.js`) in every repository: mode badge, paper panel, wallet
  and gas with a top-up warning, equity curve, positions, last AI decision,
  operation history, errors. Only the accent color and the icon change.
- **Protected commands.** Every endpoint that acts (`/api/run`, `pause`,
  `resume`, `release_funds`, ...) goes through the same check
  (`dashboard_auth.py`, identical in every repository): they stay disabled
  until `DASHBOARD_RUN_TOKEN` is set.
- **Telegram.** A report after every cycle, error alerts, and commands
  accepted only from the configured chat.
- **Deployment.** Python, SQLite, Docker; `captain-definition` for
  [CapRover](https://caprover.com). State persists in `/app/data`.

> The individual agents' READMEs are written in Italian for now.

## Getting started

1. Pick an agent and follow its README (`.env.example` lists every variable).
2. Run it in **paper trading** and let it work for a few days: the dashboard
   shows P&L, simulated costs and decisions.
3. Only then go live, with a **dedicated wallet** for each agent and small
   amounts.
4. Once several agents are running, the
   [coordinator](https://github.com/scobru/intelligent-trading-agent-coordinator)
   brings them together in a single dashboard and moves capital between them.

## Single deploy

Every agent also lives in this repo under `agents/<id>/` (imported with
`git subtree`, history included). `run.py` starts only the strategies you list,
in one container, with one `.env`:

```bash
cp .env.example .env   # set STRATEGIES=coordinator,dca,lp and the keys
docker compose up -d --build
```

- `STRATEGIES`: any of `coordinator, perp, yield, neutral, lp, dca, degen`.
- Per-strategy settings use the prefix `AGENT_<ID>_`: `AGENT_DCA_PRIVATE_KEY`
  becomes `PRIVATE_KEY` for dca only. A global `PRIVATE_KEY` is ignored, so
  each strategy keeps its own wallet. Sub-agents never see other agents' keys.
- Each strategy still runs its own `start.sh` as a separate process: one crash
  does not stop the others, and `run.py` restarts it after 30s.
- Ports: coordinator 3000 (exposed), perp 3001, yield 3002, neutral 3003,
  lp 3004, dca 3005, degen 3006 (internal, the coordinator reads them).
- State lives in the `/data/<id>` volume. On CapRover add a persistent
  directory with path `/data` (App Configs → Persistent Directories), otherwise
  every redeploy wipes positions, paper books and history.
- Paper mode: each strategy simulates on its own book, but the coordinator
  counts for it only the capital its ledger assigned to it, times the
  strategy's paper return. Transfers between strategies move that ledger.
- The coordinator shows and allocates capital only across the strategies in
  `STRATEGIES`. Each card has an "Apri Dashboard" button that opens
  `http://<host you opened the coordinator on>:<agent port>`. Publish those
  ports (docker-compose `ports`, or CapRover App Configs → Port Mapping, e.g.
  3001→3001 … 3006→3006). Set `AGENT_<ID>_PUBLIC_URL` to use another address.
- At startup `run.py` warns, once per strategy, about a missing wallet or
  `OPENROUTER_API_KEY`.
- The coordinator dashboard starts at once; its first cycle waits
  `COORDINATOR_START_DELAY` seconds (default 180) for the strategies. It also
  skips auto-rebalancing while any strategy is offline: an agent that has not
  reported yet reads as $0 and would otherwise be funded.
- Telegram commands: one bot token allows one listener, so a strategy listens
  only if it has its own `AGENT_<ID>_TELEGRAM_BOT_TOKEN`. Notifications work
  with the shared token.

## ⚠️ Disclaimer

This software is experimental and provided "as is", without warranty of any
kind (see the MIT license). It is not financial advice nor an invitation to
invest.

- **You can lose money.** Bugs, wrong model decisions, slippage, protocol
  exploits, manipulated oracles and liquidations can cause the loss of some or
  all of your capital.
- **Decisions are made by an LLM.** It can be wrong or behave unpredictably:
  the executor's limits reduce the damage, they do not eliminate it. Past
  results, paper ones included, do not guarantee future ones.
- **Start with paper or dry-run.** When live, use a wallet dedicated to the
  bot, with amounts you can afford to lose, and never reuse that private key
  elsewhere.
- **Protect your keys.** The private key belongs only in the deployment's
  environment variables: never commit it. Without `DASHBOARD_RUN_TOKEN` the
  dashboard commands stay disabled: set it to a long random value before
  exposing the dashboard to the Internet.
- **Laws and taxes.** You are responsible for complying with the rules and tax
  obligations of your country.

## License

[MIT](LICENSE)
