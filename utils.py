import streamlit as st
import yfinance as yf
import requests
import pandas as pd

import requests

def tiene_conexion():
    """Verifica si hay conexión a internet."""
    try:
        requests.get("https://finance.yahoo.com", timeout=5)
        return True
    except requests.RequestException:
        return False


def obtener_tipo_cambio_usd_mxn():
    ticker_fx = yf.Ticker("USDMXN=X")
    return ticker_fx.info.get("regularMarketPrice", 20.0)

def obtener_precio_tiempo_real(tipo, ticker):
    try:
        if tipo == "Cripto":
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ticker.lower()}&vs_currencies=usd"
            r = requests.get(url).json()
            precio_usd = r[ticker.lower()]["usd"]
            return precio_usd * obtener_tipo_cambio_usd_mxn()

        else:
            # Añadir sufijo .MX si es una acción de la Bolsa Mexicana
            ticker_ajustado = ticker
            if tipo == "Acción/ETF" and not ticker.endswith(".MX"):
                ticker_ajustado = f"{ticker}.MX"

            info = yf.Ticker(ticker_ajustado).info
            precio = info.get("regularMarketPrice")
            moneda = info.get("currency", "USD")

            if precio is None:
                return None

            if moneda == "MXN":
                return precio
            elif moneda == "USD":
                return precio * obtener_tipo_cambio_usd_mxn()
            else:
                return precio  # sin conversión si no se puede determinar

    except Exception:
        return None


def add_asset_form():
    st.subheader("➕ Agregar nuevo activo")

    tipo = st.selectbox("Tipo de activo", ["Acción/ETF", "Cripto", "CETES","Inmueble", "Otro"])
    ticker = st.text_input(f"Ingrese nombre o ticker ticker de {tipo}")

    usar_precio_rt=tipo in ["Acción/ETF","Cripto"]

    value= usar_precio_rt and tiene_conexion()

    realtime = st.checkbox("Obtener precio en tiempo real", disabled=not value)

    if not tiene_conexion():
        st.warning("⚠️ No hay conexión a internet. Solo puedes ingresar el precio manualmente.")
    
    if not usar_precio_rt:
        st.warning("⚠️ Introduce manualmente el precio de compra de tu activo")

    precio_mostrar = None
    sector_detectado = ""

    if realtime and ticker:
        precio = obtener_precio_tiempo_real(tipo, ticker)
        if precio:
            st.success(f"💲 Precio actual de {ticker.upper()}: ${precio:.4f}")
            precio_mostrar = precio

            # Solo intentar obtener el sector si es Acción/ETF
            if tipo == "Acción/ETF":
                try:
                    info = yf.Ticker(ticker).info
                    sector_detectado = info.get("sector", "")
                    if sector_detectado:
                        st.info(f"🏷️ Sector detectado: {sector_detectado}")
                    else:
                        st.warning("No se pudo detectar el sector automáticamente.")
                except Exception:
                    st.warning("Error al obtener información del sector.")
        else:
            st.warning("No se pudo obtener el precio automáticamente.")

    if not precio_mostrar:
        precio_mostrar = st.number_input("Precio de compra", min_value=0.0, format="%.4f")

    cantidad = st.number_input("Cantidad", min_value=0.0, format="%.6f")
    operacion = st.selectbox("Operación", ["Compra", "Venta"])
    fecha = st.date_input("Fecha de la operación")
    plataforma= st.text_input("Plataforma de compra (GBM,Bitso,etc)")

    # Campo editable para sector, por si se detectó o si se quiere añadir manualmente
    sector = st.text_input("Sector (opcional)", value=sector_detectado)

    # Comisiones
    usa_comision = st.checkbox("¿Incluyó comisión?")
    comision_pct = 0.0
    if usa_comision:
        comision_pct = st.number_input("Porcentaje de comisión (%)", min_value=0.0, max_value=100.0, step=0.1)

    if st.button("Agregar activo"):
        if not ticker:
            st.error("Ticker requerido.")
            return None
        return {
            "Tipo": tipo,
            "Activo": ticker.upper(),
            "Cantidad": cantidad,
            "Precio": precio_mostrar,
            "Plataforma":plataforma,
            "Operación": operacion,
            "Fecha": pd.to_datetime(fecha),
            "Sector": sector,
            "Comisión (%)": comision_pct if usa_comision else 0.0
        }

    return None


def obtener_precios_actuales_unicos(data):
    precios = {}
    for _, row in data.iterrows():
        ticker, tipo = row["Activo"], row["Tipo"]
        if ticker not in precios:
            precios[ticker] = obtener_precio_tiempo_real(tipo, ticker) or 0.0
    return precios

def agregar_valor_actual(data):
    precios = obtener_precios_actuales_unicos(data)
    data["Precio Actual"] = data["Activo"].map(precios)
    data["Valor Actual"] = data["Cantidad"] * data["Precio Actual"]
    data["Valor Compra"] = data["Cantidad"] * data["Precio"]
    data["Ganancia/Pérdida"] = data["Valor Actual"] - data["Valor Compra"]
    return data
