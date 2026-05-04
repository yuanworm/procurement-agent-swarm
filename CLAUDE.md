# Procurement Agent Swarm

## The Goal
Automated procurement for business laptops.

## The Team

- **Scout** — Finds tenders on GeBIZ.
- **Researcher** — Extracts specs from detail pages.
- **Writer** — Drafts proposals based on specs.

## Code Style

- Use Python 3.12+ for all agents.
- Use Playwright for all web tasks (scraping, navigation, screenshots).

## Automated Workflow

The swarm runs a hands-off loop. Each agent reads from the previous agent's output file and writes to its own. No agent skips a step or reads from a source other than the one defined below.

```
Scout  ──────────►  scouts/found_tenders.json
                            │
Researcher  ◄───────────────┘
     │
     └──────────►  scouts/tender_summaries.md
                            │
Writer  ◄───────────────────┘
     │
     └──────────►  proposals/new_bid.md
                            │
Reviewer  ◄─────────────────┘
     │
     └──────────►  proposals/audit.txt
                            │
                    ⛔ STOP — awaiting APPROVED
```

**Rules:**
- Scout saves raw results to `scouts/found_tenders.json`. Overwrites on each run.
- Researcher reads `found_tenders.json`, visits detail pages, and appends to `scouts/tender_summaries.md`.
- Writer reads `tender_summaries.md` and drafts `proposals/new_bid.md`. Never submits.
- Reviewer reads `new_bid.md` and writes findings to `proposals/audit.txt`. Flags issues clearly.
- The loop halts after Reviewer writes `audit.txt`. A human must type `APPROVED` to proceed.

## Safety

Never submit a proposal without a human typing `APPROVED`.

If the human does not explicitly type `APPROVED`, stop and wait. No exceptions.
