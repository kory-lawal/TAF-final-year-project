import sys
import pathlib

# Ensure the repo root is importable so `import app...` resolves in tests,
# mirroring the sys.path tweak app/main.py does at runtime.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
