#!/usr/bin/env python3
import os, sys, importlib, pkgutil, traceback

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
print("Working dir:", os.getcwd())
try:
    import modules
except Exception as e:
    print("ERROR: cannot import 'modules' package:", e)
    sys.exit(1)

print("Modules directory:", modules.__path__)
any_errors = False
for m in pkgutil.iter_modules(modules.__path__):
    name = f"modules.{m.name}"
    try:
        mod = importlib.import_module(name)
        if hasattr(mod, "module"):
            print(f"[OK] {name} (found 'module')")
        else:
            print(f"[WARN] {name} (no 'module' attribute)")
    except Exception as e:
        any_errors = True
        print(f"[ERROR] {name} import failed: {e}")
        print(traceback.format_exc())

if any_errors:
    sys.exit(2)
print("Discovery finished.")
