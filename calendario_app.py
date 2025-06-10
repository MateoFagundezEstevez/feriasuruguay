import streamlit as st
import pandas as pd
from datetime import datetime
import uuid

st.set_page_config(page_title="Calendario de Ferias en Uruguay", layout="wide")
st.title("🌎 Calendario de Ferias y Eventos Comerciales en Uruguay")
st.markdown("Explorá eventos y sugerí nuevas ferias bajo un formato predefinido.")

CSV_FILE = "eventos.csv"

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(CSV_FILE)
        df['Fecha inicio'] = pd.to_datetime(df['Fecha inicio'], errors='coerce')
        df['Fecha fin'] = pd.to_datetime(df['Fecha fin'], errors='coerce')
        df['Aprobado'] = df['Aprobado'].astype(str).str.strip().str.lower().map({
            'sí': True, 'si': True, 'true': True,
            'no': False, 'false': False
        }).fillna(False)
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            "Nombre", "Fecha inicio", "Fecha fin", "Ciudad", "Departamento",
            "Sector", "Organizador", "Contacto", "Web", "Aprobado"
        ])
    return df

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# --- FILTROS MEJORADOS ---

st.header(":date: Explorá el calendario")

data = load_data()
data_aprobada = data[data['Aprobado'] == True]

with st.expander("Filtrar por criterios"):
    deptos = sorted(data_aprobada['Departamento'].dropna().unique())
    sectores = sorted(data_aprobada['Sector'].dropna().unique())

    depto_sel = st.multiselect("Departamento", options=deptos, default=deptos)
    sector_sel = st.multiselect("Sector", options=sectores, default=sectores)

    fechas = data_aprobada[['Fecha inicio', 'Fecha fin']].dropna()
    min_fecha = fechas['Fecha inicio'].min()
    max_fecha = fechas['Fecha fin'].max()
    rango_fechas = st.date_input("Rango de fechas", [min_fecha.date(), max_fecha.date()])

    # Aplicar filtros
    filtered = data_aprobada[
        data_aprobada['Departamento'].isin(depto_sel) &
        data_aprobada['Sector'].isin(sector_sel) &
        (data_aprobada['Fecha inicio'].dt.date >= rango_fechas[0]) &
        (data_aprobada['Fecha inicio'].dt.date <= rango_fechas[1])
    ]

    if st.button("Limpiar filtros"):
        filtered = data_aprobada

st.dataframe(filtered.sort_values(by="Fecha inicio"), use_container_width=True)

# --- FORMULARIO MEJORADO ---

st.header(":mailbox_with_mail: Sugerí una feria")

data_departamentos = sorted(data['Departamento'].dropna().unique())
data_sectores = sorted(data['Sector'].dropna().unique())

with st.form("sugerencia_form"):
    nombre = st.text_input("Nombre del evento *")
    fecha_inicio = st.date_input("Fecha de inicio *")
    fecha_fin = st.date_input("Fecha de fin *")
    ciudad = st.text_input("Ciudad *")
    departamento = st.selectbox("Departamento *", options=[""] + data_departamentos)
    sector = st.selectbox("Sector *", options=[""] + data_sectores)
    organizador = st.text_input("Organizador *")
    contacto = st.text_input("Email o teléfono de contacto *")
    web = st.text_input("Web o redes sociales")
    descripcion = st.text_area("Descripción breve del evento")
    enviado = st.form_submit_button("Enviar sugerencia")

    if enviado:
        errores = []
        if not nombre.strip(): errores.append("Nombre es obligatorio.")
        if fecha_fin < fecha_inicio: errores.append("Fecha fin no puede ser anterior a fecha inicio.")
        if not ciudad.strip(): errores.append("Ciudad es obligatoria.")
        if not departamento.strip(): errores.append("Departamento es obligatorio.")
        if not sector.strip(): errores.append("Sector es obligatorio.")
        if not organizador.strip(): errores.append("Organizador es obligatorio.")
        if not contacto.strip(): errores.append("Contacto es obligatorio.")

        if errores:
            for err in errores:
                st.error(err)
        else:
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

# --- MODERACIÓN MEJORADA ---

st.sidebar.header(":lock: Moderación")
password = st.sidebar.text_input("Contraseña de administrador", type="password")

if password == "admin123":
    st.sidebar.success("Acceso concedido")
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
                    st.experimental_rerun()
            with col2:
                if st.button("Eliminar", key=f"del_{idx}"):
                    if st.confirm("¿Seguro que quieres eliminar este evento?"):
                        df = df.drop(idx)
                        save_data(df)
                        st.experimental_rerun()
else:
    st.sidebar.info("Ingresá la contraseña para acceder al panel de moderación.")
