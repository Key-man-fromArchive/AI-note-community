# Bootstrap Status

## What Exists

- independent repo root
- scope and extraction docs
- simplified compose/env/install files
- extraction utility scaffold
- extraction utility defaults to `foundation` so it does not copy product code unless a draft phase is explicitly requested
- minimal backend shell for setup, auth, notes, notebooks, members, search, graph, and snapshots
- minimal backend feedback inbox with up to 3 screenshot attachments and optional GitHub issue syncing
- minimal community frontend shell with routes for login, signup, setup, notes, search, graph, feedback, members, and backup settings
- lightweight invite acceptance flow through the signup page
- Unicode-aware note search and graph tokenization for Korean and other non-ASCII note content
- setup flow now applies the created session immediately instead of redirecting back to login
- backend pytest coverage for workspace creation, invite activation, Unicode search, snapshot restore, token failure handling, feedback/GitHub issue sync, and screenshot attachment handling

## What Does Not Exist Yet

- copied backend domain routers from the private product
- copied backend models and migrations needed for the selected features
- extracted product-grade frontend feature hooks for every retained flow
- frontend automated test suite inside this repo
- production persistence, migrations, and search indexing infrastructure

## Intended Sequence

1. sync root runtime files
2. harden the independent shell until the community contract is stable
3. extract backend community surface only where reuse is worth the maintenance cost
4. extract frontend community surface only where it does not leak premium scope
5. add automated validation for the retained community flows
