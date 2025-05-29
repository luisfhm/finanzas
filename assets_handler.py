import streamlit as st
import yfinance as yf
import requests
import datetime

def obtener_tipo_cambio_usd_mxn():
    ticker_fx = yf.Ticker("USDMXN=X")
    precio_fx = ticker_fx.info.get("regularMarketPrice")
    if precio_fx:
        return precio_fx
    else:
        return 20.0  # fallback si no se obtiene el tipo de cambio

def obtener_precio_tiempo_real(tipo, ticker):
    try:
        if tipo == "Cripto":
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ticker}&vs_currencies=usd"
            r = requests.get(url).json()
            precio_usd = r[ticker.lower()]["usd"]
            # Convertir USD a MXN
            tipo_cambio = obtener_tipo_cambio_usd_mxn()
            return precio_usd * tipo_cambio

        else:
            ticker_yf = yf.Ticker(ticker)
            precio = ticker_yf.info.get("regularMarketPrice")
            moneda = ticker_yf.info.get("currency", "USD")
            if precio is None:
                return None
            if moneda == "MXN":
                return precio
            elif moneda == "USD":
                tipo_cambio = obtener_tipo_cambio_usd_mxn()
                return precio * tipo_cambio
            else:
                # Por simplicidad, si la moneda no es USD o MXN, la retornamos sin convertir
                return precio
    except Exception:
        return None


def add_asset_form():
    st.subheader("Agregar nuevo activo")

    tipo = st.selectbox("Tipo de activo", ["Cripto", "Acción/ETF", "Bono","Otro"])

    ticker = st.text_input(f"Ingrese ticker del {tipo}")

    realtime = st.checkbox("Obtener precio en tiempo real")

    precio_mostrar = None
    if realtime and ticker:
        precio_actual = obtener_precio_tiempo_real(tipo, ticker)
        if precio_actual:
            precio_mostrar = precio_actual
            st.success(f"Precio actual de {ticker}: ${precio_actual:.4f}")
        else:
            st.warning(f"No se pudo obtener el precio para {ticker}. Por favor ingrésalo manualmente.")
    
    if not precio_mostrar:
        precio_manual = st.number_input("Precio", min_value=0.0, format="%.4f")
        precio_mostrar = precio_manual

    cantidad = st.number_input("Cantidad", min_value=0.0, format="%.6f")

    operacion = st.selectbox("Operación", ["Compra", "Venta"])

    plataforma = st.text_input("Plataforma", placeholder="Ej. Binance, BMV, etc.")

    fecha = st.date_input("Fecha de la operación")

    if st.button("Agregar activo"):
        if not ticker:
            st.error("Por favor ingrese un ticker válido.")
            return None
        return {
            "Tipo": tipo,
            "Activo": ticker.upper(),
            "Cantidad": cantidad,
            "Precio": precio_mostrar,
            "Operación": operacion,
            "Fecha": fecha,
            "Valor Total": cantidad * precio_mostrar if operacion == "Compra" else -cantidad * precio_mostrar,
            "Plataforma": plataforma  
        }
    return None
