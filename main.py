import streamlit as st
import pandas as pd
from data_handler import init_data, add_entry
from visualizations import plot_gastos_por_categoria

st.set_page_config(page_title="Finanzas Personales", layout="centered")

if 'datos' not in st.session_state:
    st.session_state.datos = init_data()

st.title("💰 Gestor de Finanzas Personales")

# Formulario
st.subheader("Registrar movimiento")
with st.form("form_movimiento"):
    fecha = st.date_input("Fecha")
    categoria = st.selectbox("Categoría", ["Alquiler", "Comida", "Transporte", "Salario", "Otros"])
    tipo = st.radio("Tipo", ["Ingreso", "Gasto"])
    monto = st.number_input("Monto", min_value=0.0, format="%.2f")
    descripcion = st.text_input("Descripción", "")
    submit = st.form_submit_button("Agregar")

    if submit:
        st.session_state.datos = add_entry(st.session_state.datos, fecha, categoria, tipo, monto, descripcion)
        st.success("Movimiento agregado")

# Resumen
st.subheader("📊 Resumen")
datos = st.session_state.datos

if datos.empty:
    st.info("Agrega movimientos para ver el resumen.")
else:
    total = datos["Monto"].sum()
    ingresos = datos[datos["Tipo"] == "Ingreso"]["Monto"].sum()
    gastos = -datos[datos["Tipo"] == "Gasto"]["Monto"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Saldo total", f"${total:.2f}")
    col2.metric("Total ingresos", f"${ingresos:.2f}")
    col3.metric("Total gastos", f"${gastos:.2f}")

    st.dataframe(datos.sort_values("Fecha", ascending=False))

    st.subheader("🧾 Gastos por categoría")
    fig = plot_gastos_por_categoria(datos)
    if fig:
        st.pyplot(fig)

    st.subheader("⬇️ Exportar datos")
    csv = datos.to_csv(index=False).encode("utf-8")
    st.download_button("Descargar como CSV", csv, "finanzas.csv", "text/csv")