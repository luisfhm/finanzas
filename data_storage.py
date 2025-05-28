import pandas as pd
from pathlib import Path

DATA_PATH = Path("portafolio.csv")

def load_data():
    if DATA_PATH.exists():
        return pd.read_csv(DATA_PATH, parse_dates=["Fecha"])
    else:
        return pd.DataFrame(columns=["Fecha", "Tipo", "Activo", "Cantidad", "Valor", "Cuenta", "Descripción"])

def save_data(df):
    df.to_csv(DATA_PATH, index=False)