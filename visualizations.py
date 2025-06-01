import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import yfinance as yf
from utils import tiene_conexion

def show_summary(data):
    st.subheader("📊 Resumen del Portafolio")

    data["Sector"] = data.get("Sector", "Desconocido")
    data["Sector"] = data["Sector"].fillna("Desconocido")

    # Asegurar conversiones numéricas
    data["Precio"] = pd.to_numeric(data["Precio"], errors="coerce").fillna(0)
    data["Precio Actual"] = pd.to_numeric(data["Precio Actual"], errors="coerce").fillna(0)
    data["Cantidad"] = pd.to_numeric(data["Cantidad"], errors="coerce").fillna(0)

    # Calcular valor actual y ganancia/pérdida
    data["Valor Actual"] = data["Precio Actual"] * data["Cantidad"]
    data["Valor Compra"] = data["Precio"] * data["Cantidad"]
    data["Ganancia/Pérdida"] = data["Valor Actual"] - data["Valor Compra"]

    # Agrupar resumen
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

        # Formatear el ticker para yfinance según el tipo
        if tipo.lower() == "cripto":
            ticker_yf = f"{ticker}-USD"
        elif tipo.lower() == "acción/etf":
            ticker_yf = f"{ticker}.MX" if not ticker.endswith(".MX") else ticker
        else:
            continue  # activos que no se pueden simular por historial

        try:
            hist = yf.download(ticker_yf, start=start, end=end, progress=False)
            if hist.empty or "Close" not in hist.columns:
                st.warning(f"⚠️ No se encontraron precios para {ticker_yf}")
                continue

            precios = hist["Close"]
            valor = precios * cantidad
            valor_total_diario[ticker] = valor

        except Exception as e:
            st.warning(f"⚠️ {ticker}: Error al obtener datos ({e})")

    if not valor_total_diario.empty:
        valor_total_diario["Total"] = valor_total_diario.sum(axis=1)

        fig = px.line(valor_total_diario.reset_index(),
                      x="Date", y="Total",
                      title=f"📈 Valor del Portafolio en los últimos {dias} días",
                      labels={"Total": "Valor total (MXN)", "Date": "Fecha"},
                      markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ No se pudo generar la gráfica. Verifica los tickers o conexión.")



