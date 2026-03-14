# Extraction Matrix

## Backend Keep First

- `app/api/auth.py`
- `app/api/files.py`
- `app/api/graph.py`
- `app/api/members.py`
- `app/api/notes.py`
- `app/api/notebooks.py`
- `app/api/search.py`
- `app/api/settings.py`
- `app/api/setup.py`
- `app/api/snapshots.py`

## Frontend Keep First

- `src/App.tsx`
- `src/components/Layout.tsx`
- `src/components/Sidebar.tsx`
- `src/pages/Login.tsx`
- `src/pages/Signup.tsx`
- `src/pages/Setup.tsx`
- `src/pages/NotesWorkspace.tsx`
- `src/pages/Notebooks.tsx`
- `src/pages/NotebookDetail.tsx`
- `src/pages/Search.tsx`
- `src/pages/Graph.tsx`
- `src/pages/Members.tsx`
- `src/pages/Settings.tsx`

## Remove Early

- AI workbench and chat surfaces
- reviewer and co-scientist surfaces
- protocols, todos, feedback, operations
- compliance and governance flows
- factory and appliance-specific workflows

## Open Questions

1. Keep note-specific version history or defer it
2. Keep NAS sync or drop it entirely for the first community release
3. Keep remote backup OAuth helpers or local/manual destinations only
