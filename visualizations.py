import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

def show_summary(data):

    portfolio = data.groupby(["Activo", "Tipo"]).agg({
        "Cantidad": "sum",
        "Valor Total": "sum"
    }).reset_index()

    total_valor = portfolio["Valor Total"].sum()
    st.write(f"### Valor total del portafolio: ${total_valor:,.2f}")

    st.dataframe(portfolio)



def show_value_by_type(portfolio):
    st.subheader("📈 Valor por Tipo de Activo")

    # Agrupar valor total por tipo
    df_tipo = portfolio.groupby("Tipo")["Valor Total"].sum().reset_index()

    if df_tipo["Valor Total"].sum() == 0:
        st.info("Los valores de los activos son todos cero.")
        return

    fig, ax = plt.subplots()
    ax.pie(df_tipo["Valor Total"], labels=df_tipo["Tipo"], autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
    ax.axis('equal')
    st.pyplot(fig)

