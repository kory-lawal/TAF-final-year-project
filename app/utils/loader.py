import pandas as pd
from pathlib import Path

def load_data(language):
    # Resolve path relative to the project root (one level above `app`)
    base = Path(__file__).resolve().parents[1]
    path = base / 'data' / f"{language}.csv"
    return pd.read_csv(path)