import streamlit as st
import pandas as pd
from utils import add_asset_form, agregar_valor_actual,tiene_conexion
from visualizations import show_summary, show_sector_distribution,simulate_portfolio_history
import datetime 


st.set_page_config(page_title="📊 Portfolio Tracker", layout="centered")
st.title("📈 Tracker de Portafolio Personal")


# Cargar CSV
try:
    data = pd.read_csv("portafolio.csv", parse_dates=["Fecha"])
except FileNotFoundError:
    data = pd.DataFrame(columns=["Fecha", "Tipo", "Activo", "Cantidad", "Precio","Plataforma"])

if not tiene_conexion():
    st.warning("⚠️ Estás sin conexión. Algunas funciones como obtener precios o simulaciones no estarán disponibles.")

# Sidebar: Formulario para agregar nuevo activo
with st.sidebar:
    new_entry = add_asset_form()
    if new_entry:
        data = pd.concat([data, pd.DataFrame([new_entry])], ignore_index=True)
        data["Fecha"] = pd.to_datetime(data["Fecha"],errors='coerce')
        data.to_csv("portafolio.csv", index=False)
        st.success("Activo agregado con éxito")


if data is not None and not data.empty:
    # Convertir la columna Fecha a datetime y ordenar
    data = data.sort_values("Fecha", ascending=False)

    # Parte principal: mostrar datos y visualizaciones
    st.subheader("📋 Activos registrados")


    # Cálculo de valores actuales
    data = agregar_valor_actual(data)
    

    # Visualizaciones
    show_summary(data)
    #show_value_by_type(data)

    if tiene_conexion():
        show_sector_distribution(data)
    simulate_portfolio_history(data)
    

else:
    st.warning("No hay datos disponibles. Por favor, agrega activos en la barra lateral.")
