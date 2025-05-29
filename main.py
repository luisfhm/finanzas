import streamlit as st
import pandas as pd
from data_storage import load_data, save_data
from assets_handler import add_asset_form
from visualizations import show_summary, show_value_by_type

st.set_page_config(page_title="📊 Portfolio Tracker", layout="centered")
st.title("📈 Tracker de Portafolio Personal")


# Carga los datos guardados
data = load_data()

# Sidebar: Formulario para agregar nuevo activo
with st.sidebar:
    st.header("➕ Agregar activo")
    new_entry = add_asset_form()
    if new_entry:
        data = pd.concat([data, pd.DataFrame([new_entry])], ignore_index=True)
        data["Fecha"] = pd.to_datetime(data["Fecha"], errors="coerce")  # <- Fuerza el tipo datetime
        save_data(data)
        st.success("Activo agregado con éxito")


if data is not None and not data.empty:
    # Convertir la columna Fecha a datetime y ordenar
    data = data.sort_values("Fecha", ascending=False)

    # Parte principal: mostrar datos y visualizaciones
    st.subheader("📋 Activos registrados")


    show_summary(data)
    show_value_by_type(data)
else:
    st.warning("No hay datos disponibles. Por favor, agrega activos en la barra lateral.")
