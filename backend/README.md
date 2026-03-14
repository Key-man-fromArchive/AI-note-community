# Community Backend Shell

Current backend surface:

- auth
- feedback
- notes
- notebooks
- members
- search
- graph
- setup
- snapshots

Implementation notes:

- lightweight JSON persistence is used for now so the repo can boot independently
- password hashing uses `pbkdf2_sha256` to avoid local `bcrypt` compatibility issues
- invited members activate their account through the shared signup route
- search and graph tokenization are Unicode-aware
- feedback is stored locally first, can include up to 3 screenshot assets, and can optionally open a GitHub issue when credentials are configured

Validation:

- `cd backend && pytest tests/test_community_shell.py`

Do not import private-product routers unless they are explicitly approved for community scope.
