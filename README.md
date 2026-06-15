# 5G Migration Agent Control Tower

Local-first MVP of a decisioning layer for subscriber migration eligibility in a 5G migration program.  

## Live app

Deployed app: [Open the streamlit app](https://5g-migration-agent-control-tower.streamlit.app/)
## Problem

Subscriber eligibility and migration prioritization depend on signals spread across multiple internal systems. A rule engine alone is insufficient when cases fall into a gray zone with conflicting signals. This MVP centralizes decisioning logic in a dedicated layer rather than relying only on downstream migration tooling.

## Architecture

```
Source adapters → Canonical context → Rules engine → [Agent for ambiguous cases] → Decision combiner → MiCC stub
```


| Layer                        | Role                                                                             |
| ---------------------------- | -------------------------------------------------------------------------------- |
| **Input adapters**           | Placeholder reads from Customer360, ProvisioningHub, DeviceRegistry, CareCaseHub |
| **Context assembler**        | Builds a canonical subscriber migration context                                  |
| **Rules engine**             | Deterministic Tier 0 / Tier 2 classification for obvious cases                   |
| **Eligibility review agent** | Reviews ambiguous cases only; may recommend Tier 0, 1, or 2                      |
| **Decision combiner**        | Final tier, reason codes, confidence, action, summary                            |
| **MiCC stub**                | Simulates queue receipt and execution outcomes                                   |


## Tier logic

- **Tier 0** — obvious straight-through case
- **Tier 1** — ambiguous or assisted-handling case
- **Tier 2** — blocked / exception / failed case

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/main.py
```

## Project layout

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for module boundaries and implementation order.

## MVP constraints

- Single eligibility review agent (no multi-agent orchestration)
- Stubbed source systems and MiCC execution
- Brand as metadata with a future override hook
- Local JSON/SQLite persistence only
- No Docker or cloud dependencies required

