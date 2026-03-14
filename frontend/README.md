# Community Frontend Shell

Current frontend surface:

- login / signup / setup
- notes workspace
- search
- graph
- feedback hub
- members
- settings with backup

Implementation notes:

- setup completes into an authenticated session immediately
- signup creates the first workspace before initialization and accepts invites after initialization
- feedback has a dedicated route with recent submissions, up to 3 screenshot previews, and optional GitHub issue status
- members settings are admin-only in the shell navigation

Navigation and route loading should stay trimmed before copying any product page implementations.
