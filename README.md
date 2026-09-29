# Intelligent Trading

> ⚠️ **Software sperimentale, non consulenza finanziaria.** Questi bot operano con denaro reale su Base e possono perdere in parte o del tutto il capitale che gli affidi. Parti in paper trading o dry-run; in live usa wallet dedicati e solo importi che puoi permetterti di perdere. Dettagli nella sezione **Avvertenza** in fondo.

Una suite di **agenti di trading autonomi su [Base](https://base.org)**, ognuno
specializzato in una strategia on-chain e guidato da un LLM (via
[OpenRouter](https://openrouter.ai)), più un **coordinatore** che distribuisce
il capitale fra loro e ne controlla il rischio complessivo.

Ogni agente è un repository a sé, con il suo deploy, e si può usare anche da
solo. Il modello propone, l'esecutore dispone: ogni limite di rischio è nel
codice dell'esecutore e non si aggira dal prompt.

---

## La suite

| Agente | Strategia | Rischio | Protocolli su Base |
|---|---|---|---|
| [**perp**](https://github.com/scobru/intelligent-trading-agent-perp) | Perpetual direzionali con leva | Alto | SynFutures V3 |
| [**degen**](https://github.com/scobru/intelligent-trading-agent-degen) | Spot speculativo su token nuovi e memecoin | Molto alto | Uniswap V3, screening di sicurezza GoPlus |
| [**yield**](https://github.com/scobru/intelligent-trading-agent-yield) | Rendimento passivo su lending e vault, looping opzionale | Basso | Aave V3, Morpho, Moonwell, Compound, ERC-4626 |
| [**neutral**](https://github.com/scobru/intelligent-trading-agent-neutral) | Funding carry delta-neutral (spot lungo + perp corto) | Basso-medio | Uniswap V3 + SynFutures V3 |
| [**dca**](https://github.com/scobru/intelligent-trading-agent-dca) | DCA modulato dal Fear & Greed e ribilanciamento | Medio-basso | Uniswap V3 |
| [**lp**](https://github.com/scobru/intelligent-trading-agent-lp) | Liquidità concentrata con ricentraggio del range | Medio | Uniswap V3 |
| [**coordinator**](https://github.com/scobru/intelligent-trading-agent-coordinator) | Cabina di regia: regime di mercato, allocazione del capitale, circuit breaker, gas | — | legge e comanda gli agenti via API |

```
                    ┌──────────────────────────────┐
                    │         coordinator          │
                    │  regime · allocazione · gas  │
                    │  circuit breaker · dashboard │
                    └──────────────┬───────────────┘
            /api/status · pause · resume · release_funds
   ┌────────┬────────┬─────────────┼────────┬────────┬────────┐
   ▼        ▼        ▼             ▼        ▼        ▼
  perp    degen    yield        neutral    dca       lp
```

## Cosa hanno in comune

- **Ciclo decisionale uguale.** Scoperta dei dati di mercato → stato del
  portafoglio → uscite di rischio automatiche (prima di sentire il modello)
  → decisione dell'LLM in JSON → controlli dell'esecutore → esecuzione.
- **Tre modalità.** `PAPER_TRADING` (portafoglio virtuale con prezzi e
  rendimenti reali), `DRY_RUN` (legge la chain, stampa il piano, non firma
  nulla) e live. La modalità si vede sempre in dashboard.
- **Dashboard coerenti.** Stesso design system (`static/dashboard.css`,
  `static/dashboard.js`) in tutti i repository: badge di modalità, pannello
  paper, wallet e gas con avviso di ricarica, andamento del capitale,
  posizioni, ultima decisione AI, storico operazioni, errori. Cambiano solo
  colore d'accento e icona.
- **Comandi protetti.** Gli endpoint che agiscono (`/api/run`, `pause`,
  `resume`, `release_funds`, ...) passano tutti dallo stesso controllo
  (`dashboard_auth.py`, identico in ogni repository): senza
  `DASHBOARD_RUN_TOKEN` configurato sono disattivati.
- **Telegram.** Report di ogni ciclo, avvisi di errore e comandi accettati
  solo dalla chat configurata.
- **Deploy.** Python, SQLite, Docker; `captain-definition` per
  [CapRover](https://caprover.com). Lo stato persiste in `/app/data`.

## Come iniziare

1. Scegli un agente e segui il suo README (`.env.example` elenca tutte le
   variabili).
2. Avvialo in **paper trading** e lascialo girare qualche giorno: la dashboard
   mostra P&L, costi simulati e decisioni.
3. Passa al live solo dopo, con un **wallet dedicato** per ogni agente e
   importi piccoli.
4. Con più agenti in funzione, il [coordinator](https://github.com/scobru/intelligent-trading-agent-coordinator)
   li mette insieme in un'unica dashboard e sposta il capitale fra loro.

## ⚠️ Avvertenza

Questo software è sperimentale ed è fornito "così com'è", senza garanzie di alcun tipo
(vedi la licenza MIT). Non è consulenza finanziaria né un invito a investire.

- **Puoi perdere denaro.** Bug, decisioni sbagliate del modello, slippage, exploit dei protocolli,
  oracoli manipolati e liquidazioni possono far perdere in parte o del tutto il capitale.
- **Le decisioni le prende un LLM.** Può sbagliare o comportarsi in modo imprevedibile: i limiti
  dell'esecutore riducono il danno, non lo azzerano. I rendimenti passati, anche in paper, non
  garantiscono quelli futuri.
- **Parti in paper o dry-run.** In live usa un wallet dedicato al bot, con importi che puoi
  permetterti di perdere, e non riutilizzare quella chiave privata altrove.
- **Proteggi le chiavi.** La chiave privata va solo nelle variabili d'ambiente del deploy: non
  committarla mai. Senza `DASHBOARD_RUN_TOKEN` i comandi della dashboard restano disattivati:
  impostalo con un valore lungo e casuale prima di esporla su Internet.
- **Leggi e tasse.** Sei responsabile del rispetto delle norme e degli obblighi fiscali del tuo paese.

## Licenza

[MIT](LICENSE)
