import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import datetime
import tempfile
import os
import json

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Registro de Charlas de 5 Minutos", page_icon="📝", layout="centered")

st.title("📝 Registro de Charlas de 5 Minutos")
st.caption("DRS Ingeniería y Gestión")

# --- CONEXIÓN A GOOGLE CLOUD VIA SECRETS ---
@st.cache_resource
def conectar_google():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # Streamlit convierte automáticamente la sección [gcp_service_account] en un diccionario válido
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    
    gc = gspread.authorize(credentials)
    drive_service = build('drive', 'v3', credentials=credentials)
    
    return gc, drive_service

try:
    gc, drive_service = conectar_google()
    st.success("✅ Conexión con Google Cloud establecida de forma segura.")
except Exception as e:
    st.error(f"❌ Error conectando a Google: {e}")
    st.stop()

# --- FORMULARIO DE INGRESO DE DATOS ---
with st.form("form_charla"):
    st.subheader("Datos de la Charla")
    
    col1, col2 = st.columns(2)
    with col1:
        fecha = st.date_input("Fecha", datetime.date.today())
        relator = st.text_input("Nombre del Relator / Supervisor")
    with col2:
        obra = st.text_input("Obra / Proyecto")
        tema = st.text_input("Tema de la Charla de 5 Minutos")
        
    observaciones = st.text_area("Observaciones / Acuerdos", placeholder="Escribe aquí los puntos principales abordados...")
    
    st.subheader("Asistentes")
    cant_asistentes = st.number_input("Número de Asistentes", min_value=1, max_value=20, value=3, step=1)
    
    asistentes_data = []
    for i in range(int(cant_asistentes)):
        st.markdown(f"**Asistente #{i+1}**")
        c1, c2, c3 = st.columns([3, 2, 2])
        with c1:
            nombre = st.text_input(f"Nombre completo #{i+1}", key=f"nom_{i}")
        with c2:
            rut = st.text_input(f"RUT/ID #{i+1}", key=f"rut_{i}")
        with c3:
            cargo = st.text_input(f"Cargo #{i+1}", key=f"car_{i}")
        asistentes_data.append({"nombre": nombre, "rut": rut, "cargo": cargo})

    submitted = st.form_submit_button("💾 Registrar Charla y Generar PDF", use_container_width=True)

# --- PROCESAMIENTO Y GENERACIÓN DE DOCUMENTOS ---
if submitted:
    if not relator or not tema or not obra:
        st.warning("⚠️ Por favor completa los campos obligatorios (Relator, Obra y Tema).")
    else:
        with st.spinner("Procesando registro y guardando en Google Cloud..."):
            try:
                # 1. Registrar en Google Sheets
                spreadsheet_id = st.secrets["SPREADSHEET_ID"]
                sheet = gc.open_by_key(spreadsheet_id).sheet1
                
                # Fila resumen
                nombres_asistentes = ", ".join([a["nombre"] for a in asistentes_data if a["nombre"]])
                fila_registro = [
                    str(fecha),
                    obra,
                    relator,
                    tema,
                    int(cant_asistentes),
                    nombres_asistentes,
                    observaciones
                ]
                sheet.append_row(fila_registro)
                
                # 2. Generar PDF Temporal con ReportLab
                temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                doc = SimpleDocTemplate(temp_pdf.name, pagesize=letter)
                story = []
                styles = getSampleStyleSheet()
                
                # Título del PDF
                story.append(Paragraph(f"<b>REGISTRO DE CHARLA DE 5 MINUTOS</b>", styles['Title']))
                story.append(Spacer(1, 15))
                
                # Encabezado de la Charla
                info_encabezado = [
                    [Paragraph("<b>Fecha:</b>", styles['Normal']), str(fecha), Paragraph("<b>Obra/Proyecto:</b>", styles['Normal']), obra],
                    [Paragraph("<b>Relator:</b>", styles['Normal']), relator, Paragraph("<b>Tema:</b>", styles['Normal']), tema]
                ]
                tabla_enc = Table(info_encabezado, colWidths=[80, 160, 90, 160])
                tabla_enc.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('PADDING', (0,0), (-1,-1), 6),
                ]))
                story.append(tabla_enc)
                story.append(Spacer(1, 15))
                
                # Tabla de Asistentes
                story.append(Paragraph("<b>Nómina de Asistentes</b>", styles['Heading2']))
                tabla_asist_data = [["N°", "Nombre Completo", "RUT", "Cargo"]]
                for idx, asis in enumerate(asistentes_data, 1):
                    tabla_asist_data.append([str(idx), asis["nombre"], asis["rut"], asis["cargo"]])
                    
                tabla_asis = Table(tabla_asist_data, colWidths=[30, 200, 120, 140])
                tabla_asis.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.navy),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                    ('PADDING', (0,0), (-1,-1), 5),
                ]))
                story.append(tabla_asis)
                story.append(Spacer(1, 15))
                
                if observaciones:
                    story.append(Paragraph("<b>Observaciones / Acuerdos:</b>", styles['Heading3']))
                    story.append(Paragraph(observaciones, styles['Normal']))
                
                doc.build(story)
                
                # 3. Subir PDF a Google Drive
                folder_id = st.secrets["FOLDER_ID"]
                nombre_archivo_pdf = f"Charla_{fecha}_{obra}_{tema[:15]}.pdf".replace(" ", "_")
                
                file_metadata = {
                    'name': nombre_archivo_pdf,
                    'parents': [folder_id]
                }
                media = MediaFileUpload(temp_pdf.name, mimetype='application/pdf')
                archivo_subido = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                
                os.unlink(temp_pdf.name)
                
                st.balloons()
                st.success(f"🎉 ¡Charla registrada exitosamente!")
                st.info(f"📄 Se guardó la información en la planilla y el reporte PDF en Drive (`{nombre_archivo_pdf}`).")
                
            except Exception as ex:
                st.error(f"❌ Ocurrió un detalle al guardar: {ex}")
