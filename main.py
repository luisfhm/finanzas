import streamlit as st
import pandas as pd
import datetime
from utils import add_asset_form, agregar_valor_actual, tiene_conexion
from visualizations import show_summary, simulate_portfolio_history

# Configuración general
st.set_page_config(page_title="📊 Portfolio Tracker", layout="centered")
st.title("📈 Tracker de Portafolio Personal")

# Cargar datos
try:
    data = pd.read_csv("portafolio.csv", parse_dates=["Fecha"])

except FileNotFoundError:
    data = pd.DataFrame(columns=["Fecha", "Tipo", "Activo", "Cantidad", "Precio", "Plataforma"])

# Sidebar para agregar activos
with st.sidebar:
    new_entry = add_asset_form()
    if new_entry:
        data = pd.concat([data, pd.DataFrame([new_entry])], ignore_index=True)
        data["Fecha"] = pd.to_datetime(data["Fecha"], errors='coerce')
        data.to_csv("portafolio.csv", index=False)
        st.success("✅ Activo agregado con éxito")

# Validar conexión
if not tiene_conexion():
    st.warning("⚠️ Estás sin conexión. Algunas funciones como obtener precios o simulaciones no estarán disponibles.")

# Verifica que hay datos
if data is not None and not data.empty:
    data = data.sort_values("Fecha", ascending=False)
    data = agregar_valor_actual(data)

    # Asegurar columna Precio Manual
    if "Precio Manual" not in data.columns:
        data["Precio Manual"] = None

    # Usar Precio Manual si Precio Actual no está disponible
    for idx, row in data.iterrows():
        if pd.isna(row["Precio Actual"]) or row["Valor Actual"] == 0:
            if pd.notna(row["Precio Manual"]):
                data.at[idx, "Precio Actual"] = row["Precio Manual"]
                data.at[idx, "Valor Actual"] = row["Cantidad"] * row["Precio Manual"]
                data.at[idx, "Ganancia/Pérdida"] = (row["Precio Manual"] - row["Precio"]) * row["Cantidad"]
            else:
                st.warning(f"⚠️ {row['Activo']} no tiene precio actual. Puedes ingresarlo manualmente.")
                valor_manual = st.number_input(
                    f"Introduce precio actual estimado para '{row['Activo']}'",
                    min_value=0.0,
                    step=100.0,
                    key=f"manual_input_{idx}"
                )
                if valor_manual > 0:
                    data.at[idx, "Precio Manual"] = valor_manual
                    data.at[idx, "Precio Actual"] = valor_manual
                    data.at[idx, "Valor Actual"] = row["Cantidad"] * row["Precio Manual"]
                    data.at[idx, "Ganancia/Pérdida"] = (valor_manual - row["Precio"]) * row["Cantidad"]
        else:
            # Si ya hay un precio manual, ofrecer opción de actualizarlo
            if pd.notna(row["Precio Manual"]):
                st.info(f"ℹ️ {row['Activo']} tiene un precio manual registrado. Puedes actualizarlo si lo deseas.")
                nuevo_valor = st.number_input(
                    f"Actualizar precio manual para '{row['Activo']}' (actual: {row['Precio Manual']})",
                    min_value=0.0,
                    step=100.0,
                    key=f"update_manual_{idx}"
                )
                if nuevo_valor > 0 and nuevo_valor != row["Precio Manual"]:
                    data.at[idx, "Precio Manual"] = nuevo_valor
                    data.at[idx, "Precio Actual"] = nuevo_valor
                    data.at[idx, "Ganancia/Pérdida"] = (nuevo_valor - row["Precio"]) * row["Cantidad"]

    # Guardar el CSV actualizado con valores manuales
    data.to_csv("portafolio.csv", index=False)


    # Crear pestañas
    tab1, tab2, tab3 = st.tabs(["📋 Activos", "📈 Simulación", "📊 Resumen"])

    with tab1:
        st.subheader("📋 Activos Registrados")
        # Formateo de moneda
        for col in ["Precio","Precio Actual","Valor Compra", "Valor Actual", "Ganancia/Pérdida"]:
            data[col] = data[col].map("${:,.2f}".format)
        st.dataframe(data)

        st.markdown("### ✏️ Editar Activo")
        activos_disponibles = data["Activo"].astype(str) + " | " + data["Fecha"].dt.strftime("%Y-%m-%d")
        seleccion = st.selectbox("Selecciona un activo para editar", activos_disponibles)

        if seleccion:
            idx = activos_disponibles[activos_disponibles == seleccion].index[0]
            activo = data.loc[idx]

            with st.form("editar_activo"):
                nuevo_tipo = st.selectbox("Tipo", options=["Acción/ETF", "Cripto", "CETES", "Inmueble", "Otro"], index=["Acción/ETF", "Cripto", "CETES", "Inmueble", "Otro"].index(activo["Tipo"]))
                nuevo_nombre = st.text_input("Nombre del Activo", value=activo["Activo"])
                nueva_fecha = st.date_input("Fecha", value=activo["Fecha"].date())
                nueva_cantidad = st.number_input("Cantidad", value=float(activo["Cantidad"]), step=1.0)
                nuevo_precio = st.number_input("Precio de Compra", value=float(activo["Precio"]), step=1.0)
                nueva_plataforma = st.text_input("Plataforma", value=activo.get("Plataforma", ""))

                guardar = st.form_submit_button("💾 Guardar cambios")

                if guardar:
                    data.loc[idx, "Tipo"] = nuevo_tipo
                    data.loc[idx, "Activo"] = nuevo_nombre
                    data.loc[idx, "Fecha"] = pd.to_datetime(nueva_fecha)
                    data.loc[idx, "Cantidad"] = nueva_cantidad
                    data.loc[idx, "Precio"] = nuevo_precio
                    data.loc[idx, "Plataforma"] = nueva_plataforma

                    data.to_csv("portafolio.csv", index=False)
                    st.success("✅ Activo actualizado con éxito")
                    st.rerun()

        st.markdown("### 🗑️ Eliminar Activo")
        seleccion_borrar = st.selectbox(
            "Selecciona un activo para eliminar",
            activos_disponibles,
            key="select_eliminar"
        )

        if seleccion_borrar:
            idx_borrar = activos_disponibles[activos_disponibles == seleccion_borrar].index[0]
            activo_borrar = data.loc[idx_borrar]

            st.warning(f"¿Estás seguro de que deseas eliminar **{activo_borrar['Activo']}** registrado el **{activo_borrar['Fecha'].date()}**?")
            confirmar_borrado = st.button("❌ Confirmar eliminación")

            if confirmar_borrado:
                data = data.drop(idx_borrar).reset_index(drop=True)
                data.to_csv("portafolio.csv", index=False)
                st.success("✅ Activo eliminado con éxito.")
                st.rerun()

    with tab2:
        simulate_portfolio_history(data)

    with tab3:
        show_summary(data)

else:
    st.warning("No hay datos disponibles. Por favor, agrega activos en la barra lateral.")
