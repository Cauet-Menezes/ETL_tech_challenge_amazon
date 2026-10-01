"""Leitura do arquivo bruto da Amazon."""
from pathlib import Path

import pandas as pd

from src.config import RAW_CSV_ENCODING, RAW_CSV_PATH


def extract_raw_amazon(csv_path: Path = RAW_CSV_PATH) -> pd.DataFrame:
    """Lê o CSV bruto com todas as colunas como texto, sem alterar valores."""
    return pd.read_csv(csv_path, dtype=str, encoding=RAW_CSV_ENCODING)
