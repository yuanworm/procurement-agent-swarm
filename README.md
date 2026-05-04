# Procurement Agent Swarm

## Goal

Build an autonomous agent swarm that discovers, monitors, and aggregates laptop tender opportunities from government portals, procurement platforms, and supplier websites.

## Architecture

```
procurement-agent/
├── scouts/          # Agents that crawl and scrape tender sources
├── README.md
```

## How It Works

1. **Scout Agents** — Distributed crawlers that monitor tender portals for new laptop procurement listings.
2. **Parsing** — Extract structured data (title, quantity, deadline, requirements) from raw pages.
3. **Aggregation** — Deduplicate and consolidate findings into a unified tender feed.

## Sources (Planned)

- Government e-procurement portals (GeBIZ, etc.)
- Public tender databases
- Supplier RFQ platforms

## Getting Started

```bash
cd scouts
pip install -r requirements.txt
```
