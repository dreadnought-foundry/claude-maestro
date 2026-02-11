---
name: "sync-docs"
description: "Sync collaboration/ documents with HackMD team workspace (bidirectional)"
---

# Skill: Sync Docs to HackMD

Bidirectional sync between the local `collaboration/` directory and the HackMD Vericorr team workspace. Pulls notes Pete and others create on HackMD, pushes local docs up.

## Usage

- `/sync-docs` — Full bidirectional sync (pull then push)
- `/sync-docs pull` — Pull new/updated notes from HackMD to local
- `/sync-docs push` — Push new/updated local files to HackMD
- `/sync-docs status` — Show what's tracked and what's changed

## Steps

1. **Determine the sync command** from the user's request (default: full sync)

2. **Run the sync script**
   ```bash
   python3.11 scripts/sync_hackmd.py {sync|pull|push|status}
   ```

3. **Report results** to the user:
   - Files created, updated, linked, or unchanged
   - Any new notes pulled from HackMD (show titles and where they were placed)
   - Any local files pushed to HackMD

## File Placement Rules

When notes are pulled from HackMD, the script infers placement based on content:

| Content Keywords | Destination |
|-----------------|-------------|
| 811, SCADA, GIS, geohazard, data sources, integration APIs | `03-architecture/integrations/` |
| Onboarding, kickoff, data collection, go-live | `05-operations/onboarding/` |
| Persona, role matrix, platform matrix | `04-product/personas/` |
| Certificate, qualification, OQ | `04-product/certificates/` |
| PHMSA, 49 CFR, regulation, audit | `06-compliance/phmsa/` |
| Competitive analysis, market research | `04-product/competitive-analysis/` |
| Training, SOP, demo scenario | `05-operations/training/` |
| Requirements, specification, API contract | `01-requirements/technical/` |
| Meeting notes, partner feedback | `09-feedback/partner-notes/` |
| Default fallback | `07-reference/research/` |

If a pulled file ends up in the wrong place, move it manually and update `collaboration/.hackmd-sync.json` to reflect the new path (keep the same `note_id`).

## Configuration

- API token: read from `.mcp.json` (`mcpServers.hackmd.env.HACKMD_API_TOKEN`)
- Team: `vericorr`
- Tracking file: `collaboration/.hackmd-sync.json` (gitignored)
- Script: `scripts/sync_hackmd.py`
- Make targets: `make sync-docs`, `make sync-docs-push`, `make sync-docs-pull`, `make sync-docs-status`

## Automation

- **Git pre-commit hook**: automatically pushes changed `.md` files in `collaboration/` on commit
- **Make target**: `make sync-docs` for manual full sync
