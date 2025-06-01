import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import yfinance as yf
from utils import tiene_conexion

def show_summary(data):
    st.subheader("📊 Resumen del Portafolio")

    data["Sector"] = data["Sector"].fillna("Desconocido")

    # Identificar activos sin valor actual asignado automáticamente
    for i, row in data.iterrows():
        tipo = row.get("Tipo", "")
        valor_actual = row.get("Valor Actual", None)

        # Si el activo no es acción/cripto o no tiene valor actual, pedir input
        if tipo not in ["Acción/ETF", "Cripto"] or pd.isna(valor_actual):
            activo = row["Activo"]
            cantidad = row["Cantidad"]

            # Input manual por activo
            valor_unitario = st.number_input(
                f"💵 Ingresa el valor actual estimado unitario para '{activo}' ({tipo}):",
                min_value=0.0,
                value=0.0,
                step=10.0,
                key=f"manual_valor_{i}"
            )

            # Calcular y asignar el valor total estimado
            data.at[i, "Valor Actual"] = valor_unitario * cantidad

    # Si hay valores de compra faltantes, asegúrate que no causen errores
    data["Valor Compra"] = pd.to_numeric(data["Valor Compra"], errors="coerce").fillna(0)
    data["Valor Actual"] = pd.to_numeric(data["Valor Actual"], errors="coerce").fillna(0)

    # Calcular ganancia/pérdida
    data["Ganancia/Pérdida"] = data["Valor Actual"] - data["Valor Compra"]

    # Agrupar
    resumen = data.groupby(["Tipo", "Sector", "Activo"]).agg({
        "Cantidad": "sum",
        "Valor Compra": "sum",
        "Valor Actual": "sum",
        "Ganancia/Pérdida": "sum"
    }).reset_index()

    # Totales globales
    total_valor = resumen["Valor Actual"].sum()
    total_compra = resumen["Valor Compra"].sum()
    total_ganancia = resumen["Ganancia/Pérdida"].sum()

    # Mostrar resumen general
    st.markdown(f"""
    - 💰 **Valor Actual del Portafolio:** ${total_valor:,.2f}  
    - 🛒 **Valor de Compra Total:** ${total_compra:,.2f}  
    - 📈 **Ganancia/Pérdida Total:** ${total_ganancia:,.2f}
    """)

    # Formateo de moneda
    for col in ["Valor Compra", "Valor Actual", "Ganancia/Pérdida"]:
        resumen[col] = resumen[col].map("${:,.2f}".format)

    st.dataframe(resumen)




import matplotlib.pyplot as plt
import seaborn as sns

def show_sector_distribution(data):
    st.subheader("📈 Distribución del Portafolio por Sector")

    if "Sector" not in data.columns:
        st.warning("No hay información del sector disponible.")
        return

    # Agrupar por sector y sumar el valor actual
    sector_data = data.groupby("Sector")["Valor Actual"].sum().reset_index()

    if sector_data.empty:
        st.info("No hay datos de sectores para mostrar.")
        return

    # Gráfico de pastel
    fig, ax = plt.subplots()
    ax.pie(sector_data["Valor Actual"], labels=sector_data["Sector"], autopct='%1.1f%%', startangle=90)
    ax.axis("equal")
    st.pyplot(fig)

import plotly.express as px
def simulate_portfolio_history(data):
    st.subheader("📈 Simulación del Valor del Portafolio a Través del Tiempo")

    if not tiene_conexion():
        st.error("❌ No hay conexión a internet. No se pueden descargar precios en este momento.")
        return

    # Selector de tipo de activos
    tipos_disponibles = data["Tipo"].dropna().unique().tolist()
    tipos_seleccionados = st.multiselect(
        "Selecciona los tipos de activos a simular:",
        tipos_disponibles,
        default=tipos_disponibles
    )

    # Selector de ventana temporal
    dias_opciones = {
        "Últimos 30 días": 30,
        "Últimos 90 días": 90,
        "Últimos 180 días": 180,
        "Últimos 360 días": 360
    }
    dias_seleccionados = st.selectbox(
        "Selecciona el rango de tiempo para la simulación:",
        list(dias_opciones.keys()),
        index=3  # por defecto 360 días
    )
    dias = dias_opciones[dias_seleccionados]

    # Validación y limpieza de datos
    data = data.dropna(subset=["Activo", "Cantidad"])
    data["Cantidad"] = pd.to_numeric(data["Cantidad"], errors="coerce").fillna(0)
    data = data[data["Tipo"].isin(tipos_seleccionados)]

    if data.empty:
        st.warning("No hay activos con los tipos seleccionados.")
        return

    # Rango de fechas
    end = datetime.datetime.today()
    start = end - pd.DateOffset(days=dias)

    valor_total_diario = pd.DataFrame()

    for _, row in data.iterrows():
        ticker = str(row["Activo"])
        cantidad = row["Cantidad"]
        tipo = row.get("Tipo", "")

        if tipo == "Acción/ETF" and not ticker.endswith(".MX"):
            ticker_yf = ticker + ".MX"
        else:
            ticker_yf = ticker

        try:
            hist = yf.download(ticker_yf, start=start, end=end, progress=False)
            if hist.empty or "Close" not in hist.columns:
                st.warning(f"No se encontraron precios para {ticker_yf}")
                continue

            precios = hist["Close"]
            valor = precios * cantidad
            valor_total_diario[ticker] = valor

        except Exception as e:
            st.warning(f"{ticker}: Error al obtener datos ({e})")

    if not valor_total_diario.empty:
        valor_total_diario["Total"] = valor_total_diario.sum(axis=1)

        fig = px.line(valor_total_diario.reset_index(),
                      x="Date", y="Total",
                      title=f"📈 Valor del Portafolio en los últimos {dias} días",
                      labels={"Total": "Valor total (MXN)", "Date": "Fecha"},
                      markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se pudo generar la gráfica. Verifica los tickers o conexión.")


