import pandas as pd

def init_data():
    return pd.DataFrame(columns=["Fecha", "Categoría", "Tipo", "Monto", "Descripción"])

def add_entry(df, fecha, categoria, tipo, monto, descripcion):
    nuevo = pd.DataFrame({
        "Fecha": [fecha],
        "Categoría": [categoria],
        "Tipo": [tipo],
        "Monto": [monto if tipo == "Ingreso" else -monto],
        "Descripción": [descripcion]
    })
    return pd.concat([df, nuevo], ignore_index=True)