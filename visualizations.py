import streamlit as st
import matplotlib.pyplot as plt

def show_summary(df):
    if df.empty:
        st.info("Aún no hay activos registrados.")
        return

    total = df["Valor"].sum()
    st.metric("💼 Valor total del portafolio", f"${total:,.2f}")

def show_value_by_type(df):
    if df.empty:
        return

    resumen = df.groupby("Tipo")["Valor"].sum().sort_values()
    fig, ax = plt.subplots()
    resumen.plot(kind="barh", ax=ax, color="skyblue")
    ax.set_title("Distribución por tipo de activo")
    ax.set_xlabel("Valor en MXN")
    st.pyplot(fig)