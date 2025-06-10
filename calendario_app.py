import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="🌈 Calendario de Ferias en Uruguay", layout="wide")

# Título colorido y centrado con emoji
st.markdown("""
<div style="text-align:center; color:#2E86C1; font-size:32px; font-weight:bold;">
    🌎 Calendario de Ferias y Eventos Comerciales en Uruguay
</div>
""", unsafe_allow_html=True)

st.markdown("""
<p style="text-align:center; color:#566573; font-size:16px;">
    Explora eventos, filtra y sugiere nuevas ferias con facilidad y estilo.
</p>
""", unsafe_allow_html=True)

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

data = load_data()
data_aprobada = data[data['Aprobado'] == True]

# --- Sección de filtros con columnas y tooltips ---
st.header(":date: Explorá el calendario")

with st.expander("Filtrar eventos 🔍"):
    col1, col2, col3, col4 = st.columns(4)

    deptos = sorted(data_aprobada['Departamento'].dropna().unique())
    sectores = sorted(data_aprobada['Sector'].dropna().unique())

    with col1:
        depto_sel = st.multiselect(
            label="Departamento", 
            options=deptos, 
            default=deptos,
            help="Seleccioná uno o varios departamentos para filtrar."
        )
    with col2:
        sector_sel = st.multiselect(
            label="Sector", 
            options=sectores, 
            default=sectores,
            help="Elegí sectores para afinar la búsqueda."
        )
    with col3:
        fechas = data_aprobada[['Fecha inicio', 'Fecha fin']].dropna()
        min_fecha = fechas['Fecha inicio'].min()
        max_fecha = fechas['Fecha fin'].max()
        rango_fechas = st.date_input(
            "Rango de fechas",
            [min_fecha.date(), max_fecha.date()],
            help="Seleccioná el rango de fechas para los eventos."
        )
    with col4:
        if st.button("🔄 Limpiar filtros"):
            depto_sel = deptos
            sector_sel = sectores
            rango_fechas = [min_fecha.date(), max_fecha.date()]

    # Aplicar filtros
    filtered = data_aprobada[
        data_aprobada['Departamento'].isin(depto_sel) &
        data_aprobada['Sector'].isin(sector_sel) &
        (data_aprobada['Fecha inicio'].dt.date >= rango_fechas[0]) &
        (data_aprobada['Fecha inicio'].dt.date <= rango_fechas[1])
    ]

# Mostrar número de eventos encontrados
st.markdown(f"### 🎉 Se encontraron **{len(filtered)}** eventos con esos filtros.")

# Mostrar tabla con colores en aprobados (solo aprobados aquí)
def color_row(row):
    return ['background-color: #D5F5E3' if row['Aprobado'] else 'background-color: #FADBD8']*len(row)

st.dataframe(filtered.sort_values(by="Fecha inicio").style.apply(color_row, axis=1), use_container_width=True)

# --- Formulario más lindo y ordenado ---
st.header(":mailbox_with_mail: Sugerí una feria")

data_departamentos = sorted(data['Departamento'].dropna().unique())
data_sectores = sorted(data['Sector'].dropna().unique())

with st.form("sugerencia_form"):
    c1, c2 = st.columns(2)
    with c1:
        nombre = st.text_input("Nombre del evento *")
        fecha_inicio = st.date_input("Fecha de inicio *")
        fecha_fin = st.date_input("Fecha de fin *")
        ciudad = st.text_input("Ciudad *")
        departamento = st.selectbox("Departamento *", options=[""] + data_departamentos)
    with c2:
        sector = st.selectbox("Sector *", options=[""] + data_sectores)
        organizador = st.text_input("Organizador *")
        contacto = st.text_input("Email o teléfono de contacto *")
        web = st.text_input("Web o redes sociales")
        descripcion = st.text_area("Descripción breve del evento")

    enviado = st.form_submit_button("Enviar sugerencia 🚀")

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
            df_actual.to_csv(CSV_FILE, index=False)
            st.success("¡Gracias por tu sugerencia! Está pendiente de aprobación.")
            st.balloons()

# --- Sidebar moderación con mejor look ---
st.sidebar.header(":lock: Moderación")

password = st.sidebar.text_input("Contraseña de administrador", type="password")

if password == "admin123":
    st.sidebar.success("Acceso concedido")
    st.subheader(":shield: Panel de moderación")
    df = load_data()
    pendientes = df[df['Aprobado'] == False]
    st.write(f"Eventos pendientes: **{len(pendientes)}**")

    for idx, row in pendientes.iterrows():
        with st.expander(f"📌 {row['Nombre']}"):
            st.write(row.drop(labels=["Aprobado"]))
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Aprobar", key=f"ap_{idx}"):
                    df.at[idx, "Aprobado"] = True
                    df.to_csv(CSV_FILE, index=False)
                    st.experimental_rerun()
            with col2:
                if st.button("❌ Eliminar", key=f"del_{idx}"):
                    if st.confirm("¿Seguro que querés eliminar este evento?"):
                        df = df.drop(idx)
                        df.to_csv(CSV_FILE, index=False)
                        st.experimental_rerun()
else:
    st.sidebar.info("Ingresá la contraseña para acceder al panel de moderación.")
