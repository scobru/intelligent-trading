"""Single entrypoint: runs the strategies listed in STRATEGIES, each with its own env.

Each agent keeps its own start.sh, wallet and data dir; this only wires them together.
Per-agent settings: AGENT_<ID>_<VAR> becomes <VAR> for that agent only
(e.g. AGENT_DCA_PRIVATE_KEY -> PRIVATE_KEY, AGENT_LP_TRADING_INTERVAL -> TRADING_INTERVAL).
"""

import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENTS_DIR = ROOT / "agents"

# Dashboard ports match the coordinator's AGENT_<ID>_URL defaults.
PORTS = {"coordinator": 3000, "perp": 3001, "yield": 3002, "neutral": 3003, "lp": 3004, "dca": 3005, "degen": 3006}
SYNFUTURES_PORTS = {"perp": 3101, "neutral": 3102}

# Never inherited from the global env: each agent must get its own via AGENT_<ID>_<VAR>,
# otherwise strategies would share a wallet or overwrite each other's state files.
PER_AGENT_ONLY = {
    "PRIVATE_KEY", "WALLET_ADDRESS", "SYNFUTURES_PRIVATE_KEY", "SYNFUTURES_WALLET",
    "SQLITE_DB_PATH", "PAPER_STATE_PATH", "POSITIONS_PATH", "PORTFOLIO_PATH",
    "POSITION_STATE_PATH", "POSITION_META_FILE", "PORT", "DASHBOARD_PORT",
    "SYNFUTURES_PORT", "SYNFUTURES_SERVICE_URL", "TELEGRAM_LISTENER",
}


def parse_strategies(raw):
    names = [s.strip().lower() for s in raw.split(",") if s.strip()]
    unknown = [n for n in names if n not in PORTS]
    if not names or unknown:
        raise SystemExit(f"STRATEGIES must list some of {sorted(PORTS)}; got {raw!r}")
    return list(dict.fromkeys(names))


def build_env(agent, base, active):
    prefix = f"AGENT_{agent.upper()}_"
    env = {k: v for k, v in base.items() if k not in PER_AGENT_ONLY}
    if agent != "coordinator":
        # Sub-agents must not see other agents' keys; only the coordinator needs them.
        env = {k: v for k, v in env.items() if not k.startswith("AGENT_") and k not in ("MASTER_PRIVATE_KEY", "SUB_AGENTS_PRIVATE_KEY")}
    env["PORT"] = env["DASHBOARD_PORT"] = str(PORTS[agent])
    if agent in SYNFUTURES_PORTS:
        env["SYNFUTURES_PORT"] = str(SYNFUTURES_PORTS[agent])
        env["SYNFUTURES_SERVICE_URL"] = f"http://localhost:{SYNFUTURES_PORTS[agent]}"
    if agent == "coordinator":
        env["SQLITE_DB_PATH"] = str(AGENTS_DIR / "coordinator" / "data" / "coordinator.db")
        for other in active:
            if other != "coordinator":
                env.setdefault(f"AGENT_{other.upper()}_URL", f"http://localhost:{PORTS[other]}")
    # One Telegram token allows one getUpdates consumer: listen only with a dedicated token.
    env["TELEGRAM_LISTENER"] = "true" if base.get(prefix + "TELEGRAM_BOT_TOKEN") else "false"
    for k, v in base.items():
        if k.startswith(prefix) and len(k) > len(prefix):
            env[k[len(prefix):]] = v
    return env


def missing_settings(agent, env):
    """Warn-only preflight: agents re-check at every cycle, this just says it once, up front."""
    if agent == "coordinator":
        return []
    missing = []
    if not (env.get("PRIVATE_KEY") or env.get("WALLET_ADDRESS") or env.get("SYNFUTURES_WALLET")):
        p = f"AGENT_{agent.upper()}_"
        missing.append(f"{p}WALLET_ADDRESS or {p}PRIVATE_KEY")
    if not env.get("OPENROUTER_API_KEY"):
        missing.append("OPENROUTER_API_KEY")
    return missing


def _pipe(agent, stream):
    for line in iter(stream.readline, ""):
        sys.stdout.write(f"[{agent}] {line}")
        sys.stdout.flush()


def start(agent, env):
    proc = subprocess.Popen(
        ["bash", "start.sh"], cwd=AGENTS_DIR / agent, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True,
    )
    threading.Thread(target=_pipe, args=(agent, proc.stdout), daemon=True).start()
    return proc


def main():
    active = parse_strategies(os.getenv("STRATEGIES", ""))
    base = dict(os.environ)
    procs = {}
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True
        for p in procs.values():
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    for agent in active:
        env = build_env(agent, base, active)
        for m in missing_settings(agent, env):
            print(f"[run] WARNING {agent}: {m} not set, its cycles will fail", flush=True)
        procs[agent] = start(agent, env)
        print(f"[run] started {agent} on port {PORTS[agent]}", flush=True)

    # start.sh loops forever; if the script itself dies, restart only that strategy.
    while not stopping:
        time.sleep(5)
        for agent, p in list(procs.items()):
            if p.poll() is not None and not stopping:
                print(f"[run] {agent} exited ({p.returncode}), restarting in 30s", flush=True)
                time.sleep(30)
                if stopping:
                    break
                procs[agent] = start(agent, build_env(agent, base, active))
    for p in procs.values():
        p.wait()


if __name__ == "__main__":
    main()
