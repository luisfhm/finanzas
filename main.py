import streamlit as st
from data_storage import load_data, save_data
from assets_handler import add_asset_form
from visualizations import show_summary, show_value_by_type

st.set_page_config(page_title="📊 Portfolio Tracker", layout="centered")
st.title("📈 Tracker de Portafolio Personal")

data = load_data()

st.sidebar.header("➕ Agregar activo")
new_entry = add_asset_form()
if new_entry:
    data = data.append(new_entry, ignore_index=True)
    save_data(data)
    st.success("Activo agregado con éxito")

st.subheader("📋 Activos registrados")
st.dataframe(data.sort_values("Fecha", ascending=False), use_container_width=True)

show_summary(data)
show_value_by_type(data)