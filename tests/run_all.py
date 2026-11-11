"""Run all tests without pytest.

  python tests/run_all.py          # all tests
  python tests/run_all.py m1       # only Milestone 1 tests (files tests/test_m1_*.py)
"""
import importlib, os, sys, time, traceback
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
prefix = "test_" + (sys.argv[1] + "_" if len(sys.argv) > 1 else "")
failed = total = 0
for fn in sorted(f for f in os.listdir(HERE) if f.startswith(prefix) and f.endswith(".py")):
    mod = importlib.import_module(fn[:-3])
    for name in sorted(n for n in dir(mod) if n.startswith("test_") and callable(getattr(mod, n))):
        total += 1; t0 = time.time()
        try:
            getattr(mod, name)()
            print(f"PASS {fn}::{name} ({time.time() - t0:.1f}s)")
        except Exception:
            failed += 1
            print(f"FAIL {fn}::{name}"); traceback.print_exc()
print(f"\n{total - failed}/{total} tests passed")
sys.exit(1 if failed else 0)
