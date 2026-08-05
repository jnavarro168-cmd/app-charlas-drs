import os
import tempfile
from datetime import datetime
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
from fpdf import FPDF
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Registro Charla 5 Minutos - DRS",
    page_icon="📋",
    layout="centered"
)

# ==========================================
# CLASE GENERADORA DE PDF (FORMATO DRS)
# ==========================================
class PDFCharla(FPDF):
    def header(self):
        # Enmarcado del Encabezado
        self.set_line_width(0.3)
        self.rect(10, 10, 190, 25)
        self.line(60, 10, 60, 35)
        self.line(145, 10, 145, 35)
        
        # Columna 1: Logo/Nombre DRS
        self.set_xy(10, 13)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(200, 30, 30)
        self.cell(50, 5, "DRS", 0, 1, "C")
        self.set_x(10)
        self.set_font("Helvetica", "B", 6)
        self.set_text_color(100, 100, 100)
        self.cell(50, 4, "INGENIERÍA Y GESTIÓN", 0, 0, "C")
        
        # Columna 2: Título Oficial
        self.set_xy(60, 14)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(0, 0, 0)
        self.cell(85, 6, "DRS INGENIERÍA Y GESTIÓN", 0, 1, "C")
        self.set_x(60)
        self.set_font("Helvetica", "B", 8.5)
        self.cell(85, 6, "REGISTRO DE CAPACITACIÓN Y DIFUSIÓN", 0, 0, "C")
        
        # Columna 3: Código, Rev, Fecha
        self.set_font("Helvetica", "", 7.5)
        self.line(145, 18, 200, 18)
        self.line(145, 26, 200, 26)
        
        self.set_xy(146, 11)
        self.cell(53, 6, "Código: F PER 603 03", 0, 0, "L")
        self.set_xy(146, 19)
        self.cell(53, 6, "Revisión :10", 0, 0, "L")
        self.set_xy(146, 27)
        self.cell(53, 6, "Fecha: 05/02/2025", 0, 0, "L")

def generar_pdf_charla(datos, participantes, ruta_firma_relator):
    pdf = PDFCharla()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)
    
    # 1. DATOS DE LA ACTIVIDAD
    pdf.set_xy(10, 38)
    pdf.set_fill_color(180, 180, 180)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(190, 5, " 1. DATOS DE LA ACTIVIDAD", 1, 1, "L", fill=True)
    
    pdf.set_font("Helvetica", "", 7.5)
    
    # Checkboxes Actividad y Modalidad
    y_curr = pdf.get_y()
    pdf.cell(30, 8, "TIPO DE LA ACTIVIDAD:", 1, 0, "C")
    pdf.cell(65, 8, f"  [X] {datos['tipo_actividad']}", 1, 0, "L")
    pdf.cell(30, 8, "MODALIDAD:", 1, 0, "C")
    pdf.cell(65, 8, f"  [X] {datos['modalidad']}", 1, 1, "L")
    
    # Datos Relator
    pdf.cell(30, 5, "RELATOR:", 1, 0, "C")
    pdf.cell(65, 5, datos['relator'], 1, 0, "C")
    pdf.cell(30, 5, "RUT:", 1, 0, "C")
    pdf.cell(65, 5, datos['rut_relator'], 1, 1, "C")
    
    pdf.cell(30, 5, "CARGO:", 1, 0, "C")
    pdf.cell(65, 5, datos['cargo_relator'], 1, 0, "C")
    pdf.cell(30, 5, "UBICACIÓN:", 1, 0, "C")
    pdf.cell(65, 5, datos['ubicacion'], 1, 1, "C")
    
    # 2. TEMA PRINCIPAL
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(190, 5, " 2. TEMA PRINCIPAL", 1, 1, "L", fill=True)
    pdf.set_font("Helvetica", "", 7)
    pdf.multi_cell(190, 3.5, datos['tema'], 1, "L")
    
    # 3. LISTA DE PARTICIPANTES
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(190, 5, " 3. LISTA DE PARTICIPANTES", 1, 1, "L", fill=True)
    
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.cell(8, 5, "N°", 1, 0, "C")
    pdf.cell(48, 5, "NOMBRE Y APELLIDO", 1, 0, "C")
    pdf.cell(28, 5, "RUT", 1, 0, "C")
    pdf.cell(38, 5, "CARGO", 1, 0, "C")
    pdf.cell(43, 5, "PROYECTO/OBRA", 1, 0, "C")
    pdf.cell(25, 5, "FIRMA", 1, 1, "C")
    
    pdf.set_font("Helvetica", "", 6.5)
    for i in range(1, 11):
        y_pos = pdf.get_y()
        if i <= len(participantes):
            p = participantes[i-1]
            pdf.cell(8, 6.5, str(i), 1, 0, "C")
            pdf.cell(48, 6.5, p['nombre'][:30], 1, 0, "L")
            pdf.cell(28, 6.5, p['rut'], 1, 0, "C")
            pdf.cell(38, 6.5, p['cargo'][:25], 1, 0, "L")
            pdf.cell(43, 6.5, p['proyecto'][:30], 1, 0, "L")
            
            x_firma = pdf.get_x()
            pdf.cell(25, 6.5, "", 1, 1, "C")
            if os.path.exists(p['ruta_firma']):
                pdf.image(p['ruta_firma'], x=x_firma + 2, y=y_pos + 0.5, w=21, h=5.5)
        else:
            pdf.cell(8, 6.5, str(i), 1, 0, "C")
            pdf.cell(48, 6.5, "", 1, 0, "L")
            pdf.cell(28, 6.5, "", 1, 0, "C")
            pdf.cell(38, 6.5, "", 1, 0, "L")
            pdf.cell(43, 6.5, "", 1, 0, "L")
            pdf.cell(25, 6.5, "", 1, 1, "C")
            
    # Resumen inferior y firma relator
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 7)
    y_bottom = pdf.get_y()
    
    pdf.cell(32, 4.5, "N° DE PARTICIPANTES:", 1, 0, "L")
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(20, 4.5, str(len(participantes)), 1, 0, "C")
    
    pdf.set_font("Helvetica", "B", 7)
    pdf.cell(20, 4.5, "FECHA", 1, 0, "C")
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(35, 4.5, datos['fecha'], 1, 0, "C")
    
    # Recuadro Firma Relator
    pdf.rect(117, y_bottom, 83, 13.5)
    if os.path.exists(ruta_firma_relator):
        pdf.image(ruta_firma_relator, x=135, y=y_bottom + 1, w=45, h=11.5)
        
    pdf.set_xy(10, y_bottom + 4.5)
    pdf.set_font("Helvetica", "B", 7)
    pdf.cell(32, 4.5, "HORA DE INICIO:", 1, 0, "L")
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(20, 4.5, datos['hora_inicio'], 1, 0, "C")
    pdf.set_font("Helvetica", "B", 7)
    pdf.cell(20, 4.5, "HORA TERMINO:", 1, 0, "C")
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(35, 4.5, datos['hora_termino'], 1, 1, "C")
    
    pdf.set_xy(10, y_bottom + 9.0)
    pdf.set_font("Helvetica", "B", 7)
    pdf.cell(32, 4.5, "DURACION:", 1, 0, "L")
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(20, 4.5, "5 MINUTOS", 1, 0, "C")
    pdf.set_font("Helvetica", "B", 7)
    pdf.cell(20, 4.5, "HH TOTALES", 1, 0, "C")
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(35, 4.5, f"{len(participantes) * 0.08:.2f} HH", 1, 1, "C")

    output_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(output_pdf.name)
    return output_pdf.name

# ==========================================
# CONEXIÓN GOOGLE DRIVE Y SHEETS
# ==========================================
def guardar_en_google(pdf_path, datos, participantes):
    if "gcp_service_account" not in st.secrets:
        return None, None

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    
    # 1. Subir PDF a Google Drive
    drive_service = build('drive', 'v3', credentials=creds)
    folder_id = st.secrets.get("GOOGLE_DRIVE_FOLDER_ID", "")
    
    file_metadata = {
        'name': f"Charla_{datos['fecha'].replace('/', '-')}_{datos['relator']}.pdf",
        'parents': [folder_id] if folder_id else []
    }
    media = MediaFileUpload(pdf_path, mimetype='application/pdf')
    file_drive = drive_service.files().create(
        body=file_metadata, media_body=media, fields='id, webViewLink'
    ).execute()
    
    # 2. Registrar Fila en Google Sheet
    client_sheets = gspread.authorize(creds)
    sheet = client_sheets.open(st.secrets.get("GOOGLE_SHEET_NAME", "Registro_Charlas")).sheet1
    
    fila_resumen = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        datos['fecha'],
        datos['relator'],
        datos['rut_relator'],
        datos['tema'],
        len(participantes),
        file_drive.get('webViewLink', '')
    ]
    sheet.append_row(fila_resumen)
    
    return file_drive.get('webViewLink'), file_drive.get('id')

# ==========================================
# INTERFAZ STREAMLIT
# ==========================================
st.title("📋 Registro de Charla 5 Minutos")
st.caption("DRS Ingeniería y Gestión")

if "participantes" not in st.session_state:
    st.session_state.participantes = []
if "firma_relator_path" not in st.session_state:
    st.session_state.firma_relator_path = None

tab1, tab2, tab3 = st.tabs(["1. Datos & Firma Relator", "2. Asistentes y Firma", "3. Guardar y Exportar"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        tipo_actividad = st.selectbox("Tipo de Actividad", ["Charla de seguridad", "Capacitación", "Reflexión", "Reunión"])
        modalidad = st.selectbox("Modalidad", ["Presencial", "E-learning"])
        relator = st.text_input("Nombre Relator", "Karen Gonzalez Vasquez")
        rut_relator = st.text_input("RUT Relator", "16.089.633-7")
    with col2:
        cargo_relator = st.text_input("Cargo Relator", "Asesor SSOMA")
        ubicacion = st.text_input("Ubicación", "E-learning")
        fecha = st.date_input("Fecha", datetime.now()).strftime("%d/%m/%Y")
        hora_inicio = st.time_input("Hora Inicio").strftime("%H:%M horas")
        hora_termino = st.time_input("Hora Término").strftime("%H:%M horas")

    tema = st.text_area("Tema Tratado", 
                        "Se realizó la difusión de la charla de seguridad 'Seguridad Vial: Conducción Segura, Respeto de la Señalización de Tránsito y Tránsito Peatonal'...")

    st.write("✍️ **Firma del Relator:**")
    canvas_relator = st_canvas(
        stroke_width=2, stroke_color="#000000", background_color="#FFFFFF",
        height=120, width=320, key="canvas_relator"
    )

    if st.button("Guardar Firma del Relator"):
        if canvas_relator.image_data is not None:
            img = Image.fromarray(canvas_relator.image_data.astype('uint8'), 'RGBA')
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            img.save(tf.name)
            st.session_state.firma_relator_path = tf.name
            st.success("Firma del relator capturada.")

with tab2:
    st.subheader("Agregar Participante")
    with st.form("form_participante", clear_on_submit=True):
        cp1, cp2 = st.columns(2)
        with cp1:
            p_nombre = st.text_input("Nombre y Apellido")
            p_rut = st.text_input("RUT Participante")
        with cp2:
            p_cargo = st.text_input("Cargo", "Profesional de proyectos ITO QA")
            p_proyecto = st.text_input("Proyecto/Obra", "NEG31244 - Servicio de Inspecciones")

        st.write("✒️ **Firma del Participante:**")
        canvas_p = st_canvas(
            stroke_width=2, stroke_color="#000000", background_color="#FFFFFF",
            height=120, width=320, key="canvas_p"
        )

        if st.form_submit_button("➕ Registrar Firma de Participante"):
            if p_nombre and p_rut and canvas_p.image_data is not None:
                img_p = Image.fromarray(canvas_p.image_data.astype('uint8'), 'RGBA')
                tf_p = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                img_p.save(tf_p.name)
                
                st.session_state.participantes.append({
                    "nombre": p_nombre, "rut": p_rut,
                    "cargo": p_cargo, "proyecto": p_proyecto,
                    "ruta_firma": tf_p.name
                })
                st.success(f"Participante {p_nombre} agregado correctamente.")

    st.write(f"**Total registrados:** {len(st.session_state.participantes)} / 10")

with tab3:
    if st.button("🚀 Finalizar y Subir a Google Drive / Sheets", type="primary"):
        if not st.session_state.firma_relator_path:
            st.error("Falta la firma del relator en la Pestaña 1.")
        elif len(st.session_state.participantes) == 0:
            st.error("Debe firmar al menos 1 participante en la Pestaña 2.")
        else:
            datos_charla = {
                "tipo_actividad": tipo_actividad, "modalidad": modalidad,
                "relator": relator, "rut_relator": rut_relator,
                "cargo_relator": cargo_relator, "ubicacion": ubicacion,
                "fecha": fecha, "hora_inicio": hora_inicio,
                "hora_termino": hora_termino, "tema": tema
            }
            pdf_file = generar_pdf_charla(datos_charla, st.session_state.participantes, st.session_state.firma_relator_path)
            link_drive, _ = guardar_en_google(pdf_file, datos_charla, st.session_state.participantes)
            
            st.balloons()
            st.success("¡Registro de Charla completado con éxito!")
            if link_drive:
                st.markdown(f"🔗 **[Abrir Documento en Google Drive]({link_drive})**")
