import base64
import json
import datetime
import tempfile
import os
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="DRS - Registro de Capacitación y Difusión", page_icon="📝", layout="centered")

st.title("📝 Registro de Capacitación y Difusión")
st.caption("DRS Ingeniería y Gestión — Formato F PER 603 03")

# --- CONEXIÓN A GOOGLE CLOUD ---
@st.cache_resource
def conectar_google():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    b64_str = st.secrets["GOOGLE_CREDENTIALS_B64"]
    json_str = base64.b64decode(b64_str).decode("utf-8")
    creds_dict = json.loads(json_str)
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(credentials)

try:
    gc = conectar_google()
    st.success("✅ Conexión con Google Cloud establecida.")
except Exception as e:
    st.error(f"❌ Error de conexión: {e}")
    st.stop()

# --- FORMULARIO PRINCIPAL ---
with st.form("form_charla"):
    st.subheader("1. Datos de la Actividad")
    col1, col2 = st.columns(2)
    with col1:
        tipo_actividad = st.selectbox("Tipo de Actividad", ["Charla de seguridad", "Capacitación", "Reflexión", "Reunión"])
        modalidad = st.selectbox("Modalidad", ["Asistencia Presencial", "E-learning", "Interna", "Externa"])
        relator_nombre = st.text_input("Nombre del Relator")
        relator_rut = st.text_input("RUT del Relator")
    with col2:
        relator_cargo = st.text_input("Cargo del Relator", value="Asesor SSOMA")
        ubicacion_obra = st.text_input("Ubicación / Obra / Proyecto")
        fecha_act = st.date_input("Fecha", datetime.date.today())
        
    c_h1, c_h2 = st.columns(2)
    with c_h1:
        hora_inicio = st.time_input("Hora Inicio", datetime.time(9, 0))
    with c_h2:
        hora_fin = st.time_input("Hora Término", datetime.time(9, 5))

    st.subheader("2. Tema Principal")
    tema_principal = st.text_area(
        "Descripción / Difusión realizada",
        placeholder="Escriba los puntos clave abordados en la charla..."
    )

    st.subheader("3. Lista de Participantes")
    cant_asistentes = st.number_input("Número de Asistentes", min_value=1, max_value=30, value=3, step=1)

    asistentes_data = []
    for i in range(int(cant_asistentes)):
        st.markdown(f"**Participante #{i+1}**")
        ca, cb, cc = st.columns([3, 2, 2])
        with ca:
            nom = st.text_input(f"Nombre completo #{i+1}", key=f"nom_{i}")
        with cb:
            rut = st.text_input(f"RUT #{i+1}", key=f"rut_{i}")
        with cc:
            car = st.text_input(f"Cargo #{i+1}", key=f"car_{i}")
        asistentes_data.append({"nombre": nom, "rut": rut, "cargo": car})

    submitted = st.form_submit_button("💾 Registrar y Generar PDF Oficial", use_container_width=True)

# --- PROCESAMIENTO Y GENERACIÓN DEL PDF OFICIAL ---
if submitted:
    if not relator_nombre or not tema_principal or not ubicacion_obra:
        st.warning("⚠️ Por favor completa los campos obligatorios (Relator, Ubicación y Tema).")
    else:
        with st.spinner("Guardando en planilla y generando PDF oficial..."):
            try:
                # 1. Enviar a Google Sheets
                sheet = gc.open_by_key(st.secrets["SPREADSHEET_ID"]).sheet1
                nombres_asistentes = ", ".join([a["nombre"] for a in asistentes_data if a["nombre"]])
                
                fila = [
                    str(fecha_act), tipo_actividad, modalidad, ubicacion_obra,
                    relator_nombre, relator_rut, relator_cargo,
                    hora_inicio.strftime("%H:%M"), hora_fin.strftime("%H:%M"),
                    int(cant_asistentes), nombres_asistentes, tema_principal
                ]
                sheet.append_row(fila)

                # 2. Construir PDF con ReportLab (Estilo F PER 603 03)
                temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                doc = SimpleDocTemplate(
                    temp_pdf.name, pagesize=letter,
                    leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36
                )
                story = []
                styles = getSampleStyleSheet()

                # Estilos personalizados
                style_header = ParagraphStyle('HeaderTitle', parent=styles['Normal'], fontSize=10, leading=12, fontName="Helvetica-Bold", alignment=1)
                style_body_bold = ParagraphStyle('BodyBold', parent=styles['Normal'], fontSize=8, leading=10, fontName="Helvetica-Bold")
                style_body = ParagraphStyle('Body', parent=styles['Normal'], fontSize=8, leading=10)

                # --- ENCABEZADO OFICIAL ---
                header_data = [
                    [
                        Paragraph("<b>DRS INGENIERÍA Y GESTIÓN</b>", style_header),
                        Paragraph("<b>REGISTRO DE CAPACITACIÓN Y DIFUSIÓN</b>", style_header),
                        Paragraph("<b>Código:</b> F PER 603 03<br/><b>Revisión:</b> 10<br/><b>Fecha:</b> 05/02/2025", style_body)
                    ]
                ]
                t_header = Table(header_data, colWidths=[150, 240, 150])
                t_header.setStyle(TableStyle([
                    ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('PADDING', (0,0), (-1,-1), 4),
                ]))
                story.append(t_header)
                story.append(Spacer(1, 10))

                # --- SECCIÓN 1: DATOS DE LA ACTIVIDAD ---
                story.append(Paragraph("<b>1. DATOS DE LA ACTIVIDAD</b>", style_body_bold))
                sec1_data = [
                    [Paragraph("<b>TIPO DE ACTIVIDAD:</b>", style_body), tipo_actividad, Paragraph("<b>MODALIDAD:</b>", style_body), modalidad],
                    [Paragraph("<b>RELATOR:</b>", style_body), f"{relator_nombre} (RUT: {relator_rut})", Paragraph("<b>CARGO:</b>", style_body), relator_cargo],
                    [Paragraph("<b>UBICACIÓN / OBRA:</b>", style_body), ubicacion_obra, Paragraph("<b>FECHA:</b>", style_body), str(fecha_act)]
                ]
                t_sec1 = Table(sec1_data, colWidths=[110, 160, 90, 180])
                t_sec1.setStyle(TableStyle([
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
                    ('BACKGROUND', (2,0), (2,-1), colors.whitesmoke),
                    ('PADDING', (0,0), (-1,-1), 4),
                ]))
                story.append(t_sec1)
                story.append(Spacer(1, 10))

                # --- SECCIÓN 2: TEMA PRINCIPAL ---
                story.append(Paragraph("<b>2. TEMA PRINCIPAL</b>", style_body_bold))
                t_sec2 = Table([[Paragraph(tema_principal, style_body)]], colWidths=[540])
                t_sec2.setStyle(TableStyle([
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('PADDING', (0,0), (-1,-1), 6),
                ]))
                story.append(t_sec2)
                story.append(Spacer(1, 10))

                # --- SECCIÓN 3: LISTA DE PARTICIPANTES ---
                story.append(Paragraph("<b>3. LISTA DE PARTICIPANTES</b>", style_body_bold))
                part_data = [["N°", "NOMBRE Y APELLIDO", "RUT", "CARGO", "PROYECTO / OBRA", "FIRMA"]]
                
                for idx, a in enumerate(asistentes_data, 1):
                    part_data.append([str(idx), a["nombre"], a["rut"], a["cargo"], ubicacion_obra, ""])
                
                # Rellenar filas vacías hasta completar 10 filas estándar
                for idx in range(len(asistentes_data) + 1, 11):
                    part_data.append([str(idx), "", "", "", "", ""])

                t_part = Table(part_data, colWidths=[25, 145, 80, 110, 110, 70])
                t_part.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#002060')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                    ('ALIGN', (0,0), (0,-1), 'CENTER'),
                    ('PADDING', (0,0), (-1,-1), 4),
                ]))
                story.append(t_part)
                story.append(Spacer(1, 10))

                # --- RESUMEN Y TIEMPOS ---
                resumen_data = [
                    [
                        f"N° DE PARTICIPANTES: {cant_asistentes}",
                        f"FECHA: {fecha_act}",
                        f"HORA INICIO: {hora_inicio.strftime('%H:%M')}",
                        f"HORA TÉRMINO: {hora_fin.strftime('%H:%M')}"
                    ]
                ]
                t_resumen = Table(resumen_data, colWidths=[135, 135, 135, 135])
                t_resumen.setStyle(TableStyle([
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('PADDING', (0,0), (-1,-1), 4),
                ]))
                story.append(t_resumen)

                doc.build(story)

                with open(temp_pdf.name, "rb") as f:
                    pdf_bytes = f.read()
                os.unlink(temp_pdf.name)

                st.balloons()
                st.success("🎉 ¡Registro grabado con éxito en Google Sheets!")
                
                nombre_pdf = f"F_PER_603_03_{fecha_act}_{ubicacion_obra}.pdf".replace(" ", "_")
                st.download_button(
                    label="📥 Descargar PDF Formato F PER 603 03",
                    data=pdf_bytes,
                    file_name=nombre_pdf,
                    mime="application/pdf",
                    use_container_width=True
                )

            except Exception as ex:
                st.error(f"❌ Ocurrió un error al procesar el registro: {ex}")
