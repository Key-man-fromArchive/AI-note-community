# AI Note Community

Community edition scaffold for an independent note workspace derived from LabNote AI.

## Product Boundary

This repository is intentionally limited to five areas:

1. Note editing
2. Member management
3. Backup and restore
4. Embedding search
5. Note graph

Community feedback is also treated as a first-class workflow, including up to 3 screenshot attachments and an optional GitHub issue bridge for faster triage.

Everything else from the main product stays out of scope for this repo.

## Non-Goals

- AI librarian chat
- AI reviewer
- AI co-scientist
- Protocol library
- Zotero integration
- Compliance and enterprise controls
- Factory appliance activation
- Billing and feature gates

## Current Status

This repo now includes a runnable community shell:

- minimal FastAPI backend for auth, setup, notes, members, search, graph, and snapshots
- minimal React frontend for login, setup, notes, search, graph, feedback, members, and backup settings
- backend pytest coverage for the core shell flows
- repo-level scope and extraction docs
- licensing and git hygiene

The current implementation is intentionally independent and lightweight. It is not yet a product-grade extraction of the private backend domain stack.

## Suggested Next Steps

1. Harden the current backend shell with tests and stable persistence contracts
2. Decide which private-domain modules should be extracted versus reimplemented
3. Replace lightweight placeholders only where the community boundary is already clear
4. Validate the split before importing any premium-adjacent code

## Source Product

The source of truth for extraction is the private `labnote-ai` codebase. This repo should stay independent and community-scoped.
