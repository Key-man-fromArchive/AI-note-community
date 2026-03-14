from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _reload_app_modules() -> ModuleType:
    importlib.invalidate_caches()
    for name in [module_name for module_name in sys.modules if module_name == "app" or module_name.startswith("app.")]:
        sys.modules.pop(name, None)
    return importlib.import_module("app.main")


@pytest.fixture
def app_modules(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[ModuleType, ModuleType]:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    main_module = _reload_app_modules()
    store_module = importlib.import_module("app.store")
    return main_module, store_module
