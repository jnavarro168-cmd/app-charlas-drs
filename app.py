import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json

# Configuración de página
st.set_page_config(page_title="Gestión de Charlas", layout="wide")

# ==========================================
# 1. AUTENTICACIÓN Y CONEXIÓN A GOOGLE SHEETS
# ==========================================
@st.cache_resource
def get_gspread_client():
    """
    Carga las credenciales desde st.secrets['gcp_service_account'],
    corrige los saltos de línea de private_key y retorna la conexión gspread.
    """
    # Convertir el Secret local/cloud a un diccionario de Python
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # Corregir saltos de línea en la clave privada para evitar error InvalidData(Invalid padding)
    if "private_key" in creds_dict and "\\n" in creds_dict["private_key"]:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    # Definir los alcances (scopes) necesarios para Google Sheets y Drive
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Crear credenciales
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    
    # Autorizar y retornar cliente de gspread
    return gspread.authorize(credentials)

def guardar_en_google_sheets(datos_registro):
    """
    Guarda una nueva fila de datos en la hoja de cálculo configurada.
    """
    try:
        gc = get_gspread_client()
        # Abrir libro por su ID desde los Secrets
        sheet = gc.open_by_key(st.secrets["GOOGLE_SHEETS_ID"]).sheet1
        
        # Insertar los datos como nueva fila
        sheet.append_row(datos_registro)
        return True, "Registro guardado exitosamente en Google Sheets."
    except Exception as e:
        return False, f"Error al guardar en Google Sheets: {str(e)}"

# ==========================================
# 2. LÓGICA DE LA APLICACIÓN (INTERFACE)
# ==========================================
st.title("Gestión y Registro de Charlas")

st.subheader("3. Guardar y Procesar Registro")

if st.button("🚀 Guardar Charla y Generar Registro", type="primary"):
    # Ejemplo de datos a registrar (ajusta según las variables de tu formulario)
    # Ejemplo: ["2026-08-17", "Charla de Seguridad", "Expositor Ejemplo", "Estado Guardado"]
    datos = [
        "2026-08-17", 
        "Charla de Seguridad", 
        "Expositor Ejemplo"
    ]
    
    # Guardar en Google Sheets
    exito, mensaje = guardar_en_google_sheets(datos)
    
    if exito:
        st.success(mensaje)
    else:
        st.error(mensaje)
