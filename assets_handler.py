import streamlit as st
import pandas as pd
from datetime import date

def add_asset_form():
    with st.form("add_asset"):
        fecha = st.date_input("Fecha", value=date.today())
        tipo = st.selectbox("Tipo de activo", ["CETES", "Bolsa", "Cripto", "Otros"])
        activo = st.text_input("Nombre del activo (ej. BTC, AAPL, CETE28)")
        cantidad = st.number_input("Cantidad", min_value=0.0)
        valor = st.number_input("Valor total (MXN)", min_value=0.0)
        cuenta = st.text_input("Cuenta o plataforma")
        descripcion = st.text_input("Descripción (opcional)", "")
        submitted = st.form_submit_button("Agregar")

        if submitted:
            return {
                "Fecha": fecha,
                "Tipo": tipo,
                "Activo": activo,
                "Cantidad": cantidad,
                "Valor": valor,
                "Cuenta": cuenta,
                "Descripción": descripcion
            }
    return None