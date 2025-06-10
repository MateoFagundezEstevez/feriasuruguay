import streamlit as st
import pandas as pd
from datetime import datetime
import uuid

# Título y descripción
st.set_page_config(page_title="Calendario de Ferias en Uruguay", layout="wide")
st.title("🌎 Calendario de Ferias y Eventos Comerciales en Uruguay")
st.markdown("Esta plataforma permite explorar eventos y sugerir nuevas ferias bajo un formato predefinido.")

# Nombre del archivo CSV de eventos
CSV_FILE = "eventos.csv"

# Cargar datos
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(CSV_FILE, parse_dates=['Fecha inicio', 'Fecha fin'])
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Nombre", "Fecha inicio", "Fecha fin", "Ciudad", "Departamento", "Sector", "Organizador", "Contacto", "Web", "Aprobado"])
    return df

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# Mostrar calendario filtrable
st.header(":date: Explorá el calendario")
data = load_data()
data_aprobada = data[data['Aprobado'] == True]

# Filtros
with st.expander("Filtrar por criterios"):
    depto = st.selectbox("Departamento", options=["Todos"] + sorted(data_aprobada['Departamento'].dropna().unique().tolist()))
    sector = st.selectbox("Sector", options=["Todos"] + sorted(data_aprobada['Sector'].dropna().unique().tolist()))
    mes = st.selectbox("Mes", options=["Todos"] + sorted(data_aprobada['Fecha inicio'].dt.strftime("%B").unique().tolist()))

    if depto != "Todos":
        data_aprobada = data_aprobada[data_aprobada['Departamento'] == depto]
    if sector != "Todos":
        data_aprobada = data_aprobada[data_aprobada['Sector'] == sector]
    if mes != "Todos":
        data_aprobada = data_aprobada[data_aprobada['Fecha inicio'].dt.strftime("%B") == mes]

# Mostrar tabla
st.dataframe(data_aprobada.sort_values(by="Fecha inicio"), use_container_width=True)

# Formulario para sugerir eventos
st.header(":mailbox_with_mail: Sugerí una feria")
with st.form("sugerencia_form"):
    nombre = st.text_input("Nombre del evento")
    fecha_inicio = st.date_input("Fecha de inicio")
    fecha_fin = st.date_input("Fecha de fin")
    ciudad = st.text_input("Ciudad")
    departamento = st.text_input("Departamento")
    sector = st.text_input("Sector")
    organizador = st.text_input("Organizador")
    contacto = st.text_input("Email o teléfono de contacto")
    web = st.text_input("Web o redes sociales")
    enviado = st.form_submit_button("Enviar sugerencia")

    if enviado:
        nuevo_evento = pd.DataFrame([{
            "Nombre": nombre,
            "Fecha inicio": fecha_inicio,
            "Fecha fin": fecha_fin,
            "Ciudad": ciudad,
            "Departamento": departamento,
            "Sector": sector,
            "Organizador": organizador,
            "Contacto": contacto,
            "Web": web,
            "Aprobado": False
        }])
        df_actual = load_data()
        df_actual = pd.concat([df_actual, nuevo_evento], ignore_index=True)
        save_data(df_actual)
        st.success("Tu sugerencia fue enviada y está pendiente de aprobación. ¡Gracias!")

# Moderación de contenidos (acceso básico)
st.sidebar.header(":lock: Moderación")
password = st.sidebar.text_input("Contraseña de administrador", type="password")

if password == "admin123":  # Cambiar esto por una variable segura en producción
    st.subheader(":shield: Panel de moderación")
    df = load_data()
    pendientes = df[df['Aprobado'] == False]
    st.write(f"Eventos pendientes: {len(pendientes)}")

    for idx, row in pendientes.iterrows():
        with st.expander(row['Nombre']):
            st.write(row.drop(labels=["Aprobado"]))
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Aprobar", key=f"ap_{idx}"):
                    df.at[idx, "Aprobado"] = True
                    save_data(df)
                    st.success("Evento aprobado.")
            with col2:
                if st.button("Eliminar", key=f"del_{idx}"):
                    df = df.drop(idx)
                    save_data(df)
                    st.warning("Evento eliminado.")

else:
    st.sidebar.info("Ingresá la contraseña para acceder al panel de moderación.")
