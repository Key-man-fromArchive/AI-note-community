#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


FOUNDATION_FILES = [
    "backend/Dockerfile",
    "backend/alembic.ini",
    "frontend/Dockerfile",
    "frontend/.prettierrc",
    "frontend/eslint.config.js",
    "frontend/index.html",
    "frontend/nginx.conf",
    "frontend/postcss.config.js",
    "frontend/tsconfig.app.json",
    "frontend/tsconfig.json",
    "frontend/tsconfig.node.json",
    "frontend/vite.config.ts",
    "frontend/vitest.config.ts",
]

BACKEND_ALLOW = [
    "backend/app/__init__.py",
    "backend/app/config.py",
    "backend/app/constants.py",
    "backend/app/database.py",
    "backend/app/main.py",
    "backend/app/models.py",
    "backend/app/api/auth.py",
    "backend/app/api/auth_responses.py",
    "backend/app/api/deps.py",
    "backend/app/api/files.py",
    "backend/app/api/graph.py",
    "backend/app/api/graph_responses.py",
    "backend/app/api/member_responses.py",
    "backend/app/api/members.py",
    "backend/app/api/note_responses.py",
    "backend/app/api/notebook_responses.py",
    "backend/app/api/notebooks.py",
    "backend/app/api/notes.py",
    "backend/app/api/search.py",
    "backend/app/api/search_responses.py",
    "backend/app/api/settings.py",
    "backend/app/api/settings_responses.py",
    "backend/app/api/setup.py",
    "backend/app/api/setup_responses.py",
    "backend/app/api/snapshot_responses.py",
    "backend/app/api/snapshots.py",
    "backend/app/search",
    "backend/app/services/auth_service.py",
    "backend/app/services/graph_service.py",
    "backend/app/services/group_service.py",
    "backend/app/services/html_sanitizer.py",
    "backend/app/services/note_snapshot_service.py",
    "backend/app/services/note_version_service.py",
    "backend/app/services/notebook_access_control.py",
    "backend/app/services/setting_values.py",
    "backend/app/services/setup_state.py",
    "backend/app/services/snapshot",
    "backend/app/services/user_service.py",
    "backend/app/utils",
]

FRONTEND_ALLOW = [
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/src/App.tsx",
    "frontend/src/main.tsx",
    "frontend/src/index.css",
    "frontend/src/components/AdminRoute.tsx",
    "frontend/src/components/ErrorBoundary.tsx",
    "frontend/src/components/Layout.tsx",
    "frontend/src/components/LoadingSpinner.tsx",
    "frontend/src/components/MarkdownEditor.tsx",
    "frontend/src/components/MarkdownRenderer.tsx",
    "frontend/src/components/NoteCard.tsx",
    "frontend/src/components/NoteEditor.tsx",
    "frontend/src/components/NoteList.tsx",
    "frontend/src/components/ObsidianGraph.tsx",
    "frontend/src/components/QuickSwitcher.tsx",
    "frontend/src/components/SearchBar.tsx",
    "frontend/src/components/ShortcutHelp.tsx",
    "frontend/src/components/Sidebar.tsx",
    "frontend/src/components/common",
    "frontend/src/components/editor",
    "frontend/src/components/members",
    "frontend/src/components/notes",
    "frontend/src/components/settings/BackupDestinations.tsx",
    "frontend/src/components/settings/BackupEncryption.tsx",
    "frontend/src/components/settings/BackupHistory.tsx",
    "frontend/src/components/settings/BackupOAuthCredentials.tsx",
    "frontend/src/components/settings/BackupScheduleConfig.tsx",
    "frontend/src/components/settings/BackupSection.tsx",
    "frontend/src/components/settings/DestinationForm.tsx",
    "frontend/src/components/settings/GraphSettingsSection.tsx",
    "frontend/src/components/settings/SearchParamsSection.tsx",
    "frontend/src/components/settings/SettingRow.tsx",
    "frontend/src/contexts",
    "frontend/src/extensions",
    "frontend/src/hooks/useDiscovery.ts",
    "frontend/src/hooks/useGraphInsights.ts",
    "frontend/src/hooks/useGraphSearch.ts",
    "frontend/src/hooks/useMembers.ts",
    "frontend/src/hooks/useNotes.ts",
    "frontend/src/hooks/useRecentNotes.ts",
    "frontend/src/hooks/useSearch.ts",
    "frontend/src/hooks/useSearchIndex.ts",
    "frontend/src/hooks/useSnapshots.ts",
    "frontend/src/lib",
    "frontend/src/locales",
    "frontend/src/pages/Graph.tsx",
    "frontend/src/pages/Login.tsx",
    "frontend/src/pages/Members.tsx",
    "frontend/src/pages/NotebookDetail.tsx",
    "frontend/src/pages/Notebooks.tsx",
    "frontend/src/pages/NotesWorkspace.tsx",
    "frontend/src/pages/Search.tsx",
    "frontend/src/pages/Settings.tsx",
    "frontend/src/pages/Setup.tsx",
    "frontend/src/pages/Signup.tsx",
    "frontend/src/stores",
    "frontend/src/types",
]


def copy_path(source_root: Path, target_root: Path, relative_path: str) -> None:
    src = source_root / relative_path
    dst = target_root / relative_path
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)


PHASES = {
    "foundation": FOUNDATION_FILES,
    "backend-draft": FOUNDATION_FILES + BACKEND_ALLOW,
    "frontend-draft": FOUNDATION_FILES + FRONTEND_ALLOW,
    "full-draft": FOUNDATION_FILES + BACKEND_ALLOW + FRONTEND_ALLOW,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy allowlisted community files from the private LabNote AI repo."
    )
    parser.add_argument(
        "--phase",
        choices=sorted(PHASES),
        default="foundation",
        help="Extraction phase. Defaults to foundation-only for safety.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root = Path("/mnt/docker/labnote-ai")
    target_root = Path("/mnt/docker/ainote-community")

    all_paths = PHASES[args.phase]
    for relative_path in all_paths:
        copy_path(source_root, target_root, relative_path)

    print(f"Phase '{args.phase}' copied {len(all_paths)} allowlisted paths into {target_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
