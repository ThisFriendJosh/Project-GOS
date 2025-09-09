from typing import Any, Dict, List, Protocol, Tuple
from pydantic import BaseModel
import importlib
import pkgutil
import traceback

class ModuleConfig(BaseModel):
    pass

class OSINTModule(Protocol):
    id: str
    name: str
    config_schema: ModuleConfig
    default_refresh_sec: int
    async def fetch(self, cfg: ModuleConfig) -> Dict[str, Any]: ...
    def render(self, st, data: Dict[str, Any]) -> None: ...

def discover_modules() -> List[OSINTModule]:
    """Robust discovery: skip broken modules instead of failing all."""
    import modules
    found = []
    for m in pkgutil.iter_modules(modules.__path__):
        try:
            mod = importlib.import_module(f"modules.{m.name}")
            if hasattr(mod, "module"):
                found.append(mod.module)
        except Exception as e:
            # Record the import error for display in Streamlit (optional)
            _MODULE_IMPORT_ERRORS.append((m.name, traceback.format_exc()))
    return sorted(found, key=lambda x: x.name.lower())

# Keep a global list of import errors that the UI can show if desired
_MODULE_IMPORT_ERRORS: List[Tuple[str, str]] = []

def get_module_import_errors() -> List[Tuple[str, str]]:
    return _MODULE_IMPORT_ERRORS
