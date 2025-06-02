import streamlit as st
import pandas as pd
import datetime
from utils import add_asset_form, agregar_valor_actual, tiene_conexion
from visualizations import show_summary, simulate_portfolio_history
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Acceder a las variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
# Crea cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

st.set_page_config(page_title="📊 Portfolio Tracker", layout="centered")

if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state["user"] is None:
    tab_login, tab_register = st.tabs(["🔐 Iniciar sesión", "🆕 Registrarse"])

    with tab_login:
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")
        if st.button("Iniciar sesión"):
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if response.user:
                st.session_state["user"] = response.user
                st.rerun()
            else:
                st.error("Email o contraseña incorrectos")

    with tab_register:
        new_email = st.text_input("Nuevo Email")
        new_password = st.text_input("Nueva Contraseña", type="password")
        if st.button("Registrarse"):
            try:
                res = supabase.auth.sign_up({
                    "email": new_email,
                    "password": new_password
                })
                if res.user:
                    st.success("✅ Registro exitoso. Ahora puedes iniciar sesión.")
                else:
                    st.error("Error al registrar usuario.")
            except Exception as e:
                st.error(f"Error: {e}")

else:
    user = st.session_state["user"]
    st.sidebar.write(f"Usuario: {user.email}")
    if st.sidebar.button("Cerrar sesión"):
        supabase.auth.sign_out()
        st.session_state["user"] = None
        st.rerun()

    user_id = user.id
    archivo_portafolio = f"portafolio_{user_id}.csv"

    if os.path.exists(archivo_portafolio):
        data = pd.read_csv(archivo_portafolio, parse_dates=["Fecha"])
    else:
        st.info("🔄 Puedes cargar tu portafolio si ya tienes uno guardado en formato CSV.")
        uploaded_file = st.file_uploader("Cargar archivo de portafolio (.csv)", type=["csv"])

        if uploaded_file is not None:
            try:
                temp_data = pd.read_csv(uploaded_file, parse_dates=["Fecha"])
                required_cols = {"Fecha", "Tipo", "Activo", "Cantidad", "Precio", "Plataforma"}
                if required_cols.issubset(temp_data.columns):
                    temp_data.to_csv(archivo_portafolio, index=False)
                    data = temp_data
                    st.success("✅ Portafolio cargado con éxito.")
                    st.rerun()
                else:
                    st.error("❌ El archivo no contiene las columnas requeridas: " + ", ".join(required_cols))
            except Exception as e:
                st.error(f"Error al cargar archivo: {e}")
        else:
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
        tab1, tab2, tab3 = st.tabs(["📊 Resumen", "📈 Simulación","📋 Activos"])

        with tab3:
            st.subheader("📋 Activos Registrados")
            data_mostrar=data.copy()
            # Formateo de moneda
            for col in ["Precio","Precio Actual","Valor Compra", "Valor Actual", "Ganancia/Pérdida"]:
                data_mostrar[col] = data_mostrar[col].map("${:,.2f}".format)
            st.dataframe(data_mostrar)

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

        with tab1:
            show_summary(data)

    else:
        st.warning("No hay datos disponibles. Por favor, agrega activos en la barra lateral.")
