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

## Safety

Never submit a proposal without a human typing `APPROVED`.

If the human does not explicitly type `APPROVED`, stop and wait. No exceptions.
