import os
import datetime
import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from google_services import append_to_sheets, upload_pdf_to_drive

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Registro de Charlas y Capacitaciones",
    page_icon="📋",
    layout="wide"
)

def generar_pdf(datos_charla: dict, participantes: list, filename: str) -> str:
    """Genera un archivo PDF con la información de la charla y sus participantes."""
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Encabezado
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "REGISTRO DE ASISTENCIA Y CHARLA")
    
    # Datos generales de la actividad
    c.setFont("Helvetica", 10)
    y = height - 90
    c.drawString(50, y, f"Fecha: {datos_charla.get('fecha')}")
    c.drawString(300, y, f"Tipo de Actividad: {datos_charla.get('tipo_actividad')}")
    
    y -= 20
    c.drawString(50, y, f"Modalidad: {datos_charla.get('modalidad')}")
    c.drawString(300, y, f"Ubicación: {datos_charla.get('ubicacion')}")
    
    y -= 20
    c.drawString(50, y, f"Relator: {datos_charla.get('relator_nombre')} (RUT: {datos_charla.get('relator_rut')})")
    
    y -= 20
    c.drawString(50, y, f"Tema: {datos_charla.get('tema')}")

    # Línea divisoria
    y -= 20
    c.line(50, y, width - 50, y)

    # Tabla de participantes
    y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Lista de Participantes:")

    y -= 20
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y, "Nombre")
    c.drawString(200, y, "RUT")
    c.drawString(300, y, "Cargo")
    c.drawString(410, y, "Proyecto")
    c.drawString(500, y, "Estado")

    y -= 10
    c.line(50, y, width - 50, y)

    c.setFont("Helvetica", 9)
    for p in participantes:
        y -= 20
        if y < 50:  # Salto de página si se acaba el espacio
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 9)

        estado = "FIRMADO" if p.get("firmado") else "PENDIENTE"
        c.drawString(50, y, str(p.get("nombre", "")))
        c.drawString(200, y, str(p.get("rut", "")))
        c.drawString(300, y, str(p.get("cargo", "")))
        c.drawString(410, y, str(p.get("proyecto", "")))
        c.drawString(500, y, estado)

    c.save()
    return filename


# Inicializar el estado de la sesión para los participantes
if "participantes" not in st.session_state:
    st.session_state.participantes = []

st.title("📋 Registro de Charlas y Capacitaciones")

st.header("1. Datos Generales de la Actividad")
col1, col2 = st.columns(2)

with col1:
    fecha = st.date_input("Fecha", datetime.date.today())
    tipo_actividad = st.selectbox("Tipo de Actividad", ["Charla 5 Minutos", "Capacitación", "Inducción", "Taller"])
    modalidad = st.selectbox("Modalidad", ["Presencial", "Online", "Híbrida"])
    ubicacion = st.text_input("Ubicación / Sala", "Oficina Central")

with col2:
    relator_nombre = st.text_input("Nombre del Relator")
    relator_rut = st.text_input("RUT del Relator")
    tema = st.text_input("Tema / Título de la Charla")

st.divider()

st.header("2. Registro de Participantes")

# Formulario para agregar participante
with st.form("form_participante", clear_on_submit=True):
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        p_nombre = st.text_input("Nombre Completo")
    with col_p2:
        p_rut = st.text_input("RUT")
    with col_p3:
        p_cargo = st.text_input("Cargo")
    with col_p4:
        p_proyecto = st.text_input("Proyecto / Área")

    p_firmado = st.checkbox("¿Asistencia Firmada / Confirmada?", value=True)
    
    btn_agregar = st.form_submit_button("➕ Agregar Participante")
    
    if btn_agregar:
        if p_nombre and p_rut:
            st.session_state.participantes.append({
                "nombre": p_nombre,
                "rut": p_rut,
                "cargo": p_cargo,
                "proyecto": p_proyecto,
                "firmado": p_firmado
            })
            st.success(f"Participante {p_nombre} agregado correctamente.")
        else:
            st.warning("El Nombre y el RUT son obligatorios.")

# Mostrar tabla de participantes agregados
if st.session_state.participantes:
    st.subheader("Lista de Asistentes Ingresados")
    df_part = pd.DataFrame(st.session_state.participantes)
    st.dataframe(df_part, use_container_width=True)
    
    if st.button("🗑️ Limpiar Lista de Participantes"):
        st.session_state.participantes = []
        st.experimental_rerun()

st.divider()

st.header("3. Guardar y Procesar Registro")

if st.button("🚀 Guardar Charla y Generar Registro", type="primary"):
    if not relator_nombre or not tema:
        st.error("Por favor completa los campos obligatorios del relator y el tema.")
    elif not st.session_state.participantes:
        st.error("Debes agregar al menos un participante.")
    else:
        with st.spinner("Procesando datos y sincronizando con Google..."):
            datos_charla = {
                "fecha": fecha.strftime("%Y-%m-%d"),
                "tipo_actividad": tipo_actividad,
                "modalidad": modalidad,
                "relator_nombre": relator_nombre,
                "relator_rut": relator_rut,
                "ubicacion": ubicacion,
                "tema": tema
            }
            
            # 1. Guardar en Google Sheets
            try:
                sheet_id = st.secrets["GOOGLE_SHEETS_ID"]
                append_to_sheets(sheet_id, datos_charla, st.session_state.participantes)
                st.success("✅ Datos registrados exitosamente en Google Sheets.")
            except Exception as e:
                st.error(f"Error al guardar en Google Sheets: {e}")

            # 2. Generar PDF
            pdf_filename = f"Registro_{fecha.strftime('%Y%m%d')}_{tema.replace(' ', '_')}.pdf"
            generar_pdf(datos_charla, st.session_state.participantes, pdf_filename)

            # 3. Subir PDF a Google Drive
            try:
                folder_id = st.secrets["GOOGLE_DRIVE_FOLDER_ID"]
                link_pdf = upload_pdf_to_drive(pdf_filename, folder_id)
                st.success(f"✅ Documento PDF guardado en Google Drive.")
                st.markdown(f"[📄 Ver archivo subido en Google Drive]({link_pdf})")
            except Exception as e:
                st.error(f"Error al subir el archivo a Google Drive: {e}")

            # Limpiar archivo local temporal
            if os.path.exists(pdf_filename):
                os.remove(pdf_filename)
