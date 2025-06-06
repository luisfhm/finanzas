import streamlit as st
import pandas as pd
from utils import (
    add_asset_form, agregar_valor_actual, tiene_conexion,
    guardar_activo_en_supabase, obtener_activos_usuario,
    actualizar_activo_supabase, eliminar_activo_supabase,
    create_authenticated_client
)
from visualizations import show_summary, simulate_portfolio_history
from supabase import create_client
from dotenv import load_dotenv
import os
import jwt
from streamlit_cookies_manager import EncryptedCookieManager


st.set_page_config(page_title="📊 Portfolio Tracker", layout="centered")

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

cookies = EncryptedCookieManager(
    prefix="portfolio_",
    password=os.getenv("COOKIE_SECRET", "fallback_inseguro")
)
if not cookies.ready():
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# --- Helper para manejar sesión persistente ---
def guardar_token_en_session(token, user):
    st.session_state["access_token"] = token
    st.session_state["user"] = user

def limpiar_sesion():
    for k in ["access_token", "user"]:
        if k in st.session_state:
            del st.session_state[k]
    cookies["access_token"] = ""
    cookies["user_email"] = ""
    cookies.save()



# --- Manejar inicio con token guardado ---
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None
if "user" not in st.session_state:
    st.session_state["user"] = None

if "access_token" not in st.session_state or not st.session_state["access_token"]:
    # Intentar recuperar de cookie
    if cookies.get("access_token"):
        st.session_state["access_token"] = cookies.get("access_token")
        st.session_state["user"] = type("User", (), {"email": cookies.get("user_email")})()

# --- Mostrar pantalla login/registro si no hay usuario ---
if not st.session_state["user"]:
    tab_login, tab_register = st.tabs(["🔐 Iniciar sesión", "🆕 Registrarse"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Contraseña", type="password", key="login_password")
        if st.button("Iniciar sesión"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if res.user:
                    guardar_token_en_session(res.session.access_token, res.user)
                    cookies["access_token"] = res.session.access_token
                    cookies["user_email"] = email
                    cookies.save()
                    st.success("✅ Sesión iniciada")
                    st.rerun()
                else:
                    st.error("Email o contraseña incorrectos")
            except Exception as e:
                st.error(f"Error de inicio de sesión: {e}")

    with tab_register:
        new_email = st.text_input("Nuevo Email", key="reg_email")
        new_password = st.text_input("Nueva Contraseña", type="password", key="reg_password")
        if st.button("Registrarse"):
            try:
                res = supabase.auth.sign_up({"email": new_email, "password": new_password})
                if res.user:
                    st.success("✅ Registro exitoso. Ahora puedes iniciar sesión.")
                else:
                    st.error("Error al registrar usuario.")
            except Exception as e:
                st.error(f"Error al registrar usuario: {e}")

else:
    # Usuario ya autenticado
    supabase_user = create_authenticated_client(SUPABASE_URL, SUPABASE_ANON_KEY, st.session_state["access_token"])

    try:
        decoded_token = jwt.decode(st.session_state["access_token"], options={"verify_signature": False})
        user_id = decoded_token.get("sub", None)
    except Exception:
        st.error("Token inválido. Por favor, cierra sesión y vuelve a iniciar sesión.")
        limpiar_sesion()
        st.rerun()

    st.sidebar.write(f"Usuario: {st.session_state['user'].email}")
    if st.sidebar.button("Cerrar sesión"):
        limpiar_sesion()
        st.rerun()

    # Obtener activos usuario
    data = obtener_activos_usuario(supabase_user, user_id)

    # Importar CSV si portafolio vacío
    if data.empty:
        st.info("🔄 Puedes cargar tu portafolio si ya tienes uno guardado en formato CSV.")
        uploaded_file = st.file_uploader("Cargar archivo de portafolio (.csv)", type=["csv"])
        if uploaded_file is not None:
            try:
                temp_data = pd.read_csv(uploaded_file, encoding='utf-8-sig', parse_dates=["Fecha"])
                required_cols = {"Fecha", "Tipo", "Activo", "Cantidad", "Precio", "Plataforma"}
                if required_cols.issubset(temp_data.columns):
                    entries = []
                    for _, row in temp_data.iterrows():
                        entries.append({
                            "Fecha": row["Fecha"].strftime("%Y-%m-%d") if not pd.isna(row["Fecha"]) else None,
                            "Tipo": row["Tipo"],
                            "Activo": row["Activo"],
                            "Cantidad": row["Cantidad"],
                            "Precio": row["Precio"],
                            "Plataforma": row["Plataforma"],
                            "user_id": user_id
                        })
                    # Guardar en batch (si tu función lo soporta, si no iterar)
                    for entry in entries:
                        guardar_activo_en_supabase(supabase_user, entry)
                    st.success("✅ Portafolio importado con éxito.")
                    st.rerun()
                else:
                    st.error("❌ El archivo no contiene las columnas requeridas.")
            except Exception as e:
                st.error(f"Error al cargar archivo: {e}")

    # Formulario para agregar activos en sidebar
    with st.sidebar:
        new_entry = add_asset_form()
        if new_entry:
            guardar_activo_en_supabase(supabase_user, new_entry)
            st.success("✅ Activo agregado con éxito")
            st.rerun()

    # Verificar conexión
    if not tiene_conexion():
        st.warning("⚠️ Estás sin conexión. Algunas funciones no estarán disponibles.")

    if not data.empty:
        data = data.sort_values("Fecha", ascending=False)
        data = agregar_valor_actual(data)

        if "Precio Manual" not in data.columns:
            data["Precio Manual"] = None

        # Detectar activos sin precio actual
        activos_sin_precio = data[
            data["Precio Actual"].isna() | (data["Precio Actual"] == 0) | (data["Valor Actual"] == 0)
        ]["Activo"].unique()

        if len(activos_sin_precio) == 0:
            st.success("✅ Todos los activos ya tienen precios actualizados.")
        else:
            precios_manual = {}
            for activo in activos_sin_precio:
                st.markdown("### 💰 Ingresar precio manual por activo (si falta precio actual)")
                precios_manual[activo] = st.number_input(
                    f"Ingresar precio manual actual para **{activo}**",
                    min_value=0.0, format="%.2f", key=f"precio_manual_{activo}"
                )

            # Verificar si el usuario ya ingresó precios válidos para todos
            todos_tienen_precio = all(precios_manual[activo] > 0 for activo in precios_manual)

            if todos_tienen_precio:
                for idx, row in data.iterrows():
                    activo = row["Activo"]
                    if activo in precios_manual:
                        precio_manual = precios_manual[activo]
                        if pd.isna(row.get("Precio Actual")) or row.get("Precio Actual", 0) == 0 or row.get("Valor Actual", 0) == 0:
                            nuevos_valores = {
                                "Precio Manual": precio_manual,
                                "Precio Actual": precio_manual,
                                "Valor Actual": row["Cantidad"] * precio_manual,
                                "Ganancia/Pérdida": (precio_manual - row["Precio"]) * row["Cantidad"]
                            }
                            actualizar_activo_supabase(supabase_user, user_id, row["id"], nuevos_valores)

                st.success("✅ Precios manuales actualizados automáticamente.")
                data = obtener_activos_usuario(supabase_user, user_id)
                st.rerun()
            else:
                if st.button("💾 Guardar precios manuales"):
                    for idx, row in data.iterrows():
                        activo = row["Activo"]
                        if activo in precios_manual and precios_manual[activo] > 0:
                            if pd.isna(row.get("Precio Actual")) or row.get("Precio Actual", 0) == 0 or row.get("Valor Actual", 0) == 0:
                                precio_manual = precios_manual[activo]
                                nuevos_valores = {
                                    "Precio Manual": precio_manual,
                                    "Precio Actual": precio_manual,
                                    "Valor Actual": row["Cantidad"] * precio_manual,
                                    "Ganancia/Pérdida": (precio_manual - row["Precio"]) * row["Cantidad"]
                                }
                                actualizar_activo_supabase(supabase_user, user_id, row["id"], nuevos_valores)

                    st.success("✅ Precios manuales actualizados.")
                    data = obtener_activos_usuario(supabase_user, user_id)
                    st.rerun()


        # Tabs
        tab1, tab2, tab3 = st.tabs(["📊 Resumen", "📈 Simulación", "📋 Activos"])

        with tab3:
            st.subheader("📋 Activos Registrados")
            mostrar = data.copy()
            for col in ["Precio", "Precio Actual", "Valor Compra", "Valor Actual", "Ganancia/Pérdida"]:
                if col in mostrar.columns:
                    mostrar[col] = mostrar[col].map("${:,.2f}".format)
            st.dataframe(mostrar)

            st.markdown("### ✏️ Editar Activo")
            activos_disponibles = data["Activo"].astype(str) + " | " + pd.to_datetime(data["Fecha"]).dt.strftime("%Y-%m-%d")
            seleccion = st.selectbox("Selecciona un activo para editar", activos_disponibles)

            if seleccion:
                idx = activos_disponibles[activos_disponibles == seleccion].index[0]
                activo = data.loc[idx]

                with st.form("editar_activo"):
                    nuevo_tipo = st.selectbox("Tipo", ["Acción/ETF", "Cripto", "CETES", "Inmueble", "Otro"],
                                             index=["Acción/ETF", "Cripto", "CETES", "Inmueble", "Otro"].index(activo["Tipo"]))
                    nuevo_nombre = st.text_input("Nombre del Activo", value=activo["Activo"])
                    nueva_fecha = st.date_input("Fecha", value=pd.to_datetime(activo["Fecha"]).date())
                    nueva_cantidad = st.number_input("Cantidad", value=float(activo["Cantidad"]))
                    nuevo_precio = st.number_input("Precio de Compra", value=float(activo["Precio"]))
                    nueva_plataforma = st.text_input("Plataforma", value=activo.get("Plataforma", ""))
                    nuevo_sector=st.text_input("Sector", value=activo.get("Sector", ""))
                    guardar = st.form_submit_button("💾 Guardar cambios")

                    if guardar:
                        actualizado = {
                            "Tipo": nuevo_tipo,
                            "Activo": nuevo_nombre,
                            "Fecha": str(nueva_fecha),
                            "Cantidad": nueva_cantidad,
                            "Precio": nuevo_precio,
                            "Plataforma": nueva_plataforma,
                            "Sector":nuevo_sector
                        }
                        resultado = actualizar_activo_supabase(supabase_user, user_id, activo["id"], actualizado)
                        if resultado.get("success"):
                            st.success("✅ Activo actualizado con éxito")
                            st.rerun()
                        else:
                            st.error(f"❌ No se pudo actualizar el activo: {resultado.get('error')}")

            st.markdown("### 🗑️ Eliminar Activo")
            seleccion_borrar = st.selectbox("Selecciona un activo para eliminar", activos_disponibles, key="select_eliminar")

            if seleccion_borrar:
                idx_borrar = activos_disponibles[activos_disponibles == seleccion_borrar].index[0]
                activo_borrar = data.loc[idx_borrar]

                st.warning(f"¿Estás seguro de eliminar **{activo_borrar['Activo']}** del **{pd.to_datetime(activo_borrar['Fecha']).date()}**?")
                confirmar = st.button("❌ Confirmar eliminación")

                if confirmar:
                    eliminar_activo_supabase(supabase_user,user_id, activo_borrar["id"])
                    st.success("✅ Activo eliminado con éxito.")
                    st.rerun()

        with tab2:
            simulate_portfolio_history(data)

        with tab1:
            show_summary(data)
            # --- OPCIONAL: Actualización manual para activos no automáticos ---
            tipos_no_automaticos = ["CETES", "Inmueble", "Otro"]
            activos_no_auto = data[data["Tipo"].isin(tipos_no_automaticos)]

            if not activos_no_auto.empty:
                st.markdown("### ✏️ Actualizar manualmente precios de activos no automáticos")

                activos_unicos = activos_no_auto["Activo"].unique()

                for activo in activos_unicos:
                    # Obtengo las filas para ese activo
                    filas_activo = activos_no_auto[activos_no_auto["Activo"] == activo]

                    # Para valor inicial del input, puedo tomar el primer registro que tenga Precio Actual o Precio
                    first_row = filas_activo.iloc[0]
                    valor_inicial = (
                        float(first_row["Precio Actual"]) if not pd.isna(first_row["Precio Actual"])
                        else float(first_row["Precio"])
                    )

                    nuevo_precio = st.number_input(
                        f"Nuevo precio para {activo}",
                        min_value=0.0,
                        value=valor_inicial,
                        format="%.2f",
                        key=f"manual_update_{activo}"
                    )

                    if st.button(f"Actualizar precio de {activo}", key=f"btn_manual_{activo}"):
                        errores = []
                        exito = True

                        for idx, row in filas_activo.iterrows():
                            nuevos_valores = {
                                "Precio Manual": nuevo_precio,
                                "Precio Actual": nuevo_precio,
                                "Valor Actual": nuevo_precio * row["Cantidad"],
                                "Ganancia/Pérdida": (nuevo_precio - row["Precio"]) * row["Cantidad"]
                            }
                            resultado = actualizar_activo_supabase(supabase_user, user_id, row["id"], nuevos_valores)

                            if not resultado.get("success"):
                                errores.append(f"{row['Activo']} (id {row['id']}): {resultado.get('error')}")
                                exito = False

                        if exito:
                            st.success(f"✅ Precio de {activo} actualizado para todas las posiciones.")
                            st.rerun()
                        else:
                            st.error("❌ Error al actualizar algunos activos:\n" + "\n".join(errores))

    else:
        st.warning("No hay datos disponibles. Por favor, agrega activos en la barra lateral.")
