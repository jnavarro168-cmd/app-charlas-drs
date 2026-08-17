import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

def fix_pem_key(key: str) -> str:
    """
    Limpia y normaliza la clave privada PEM eliminando secuencias '\\n' 
    literales o saltos mal formateados.
    """
    if not key:
        return key
    
    # Quitar comillas o espacios residuales
    key = key.strip().strip('"').strip("'")
    
    header = "-----BEGIN PRIVATE KEY-----"
    footer = "-----END PRIVATE KEY-----"
    
    if header in key and footer in key:
        # Extraer el bloque Base64 entre el encabezado y el pie
        body = key.replace(header, "").replace(footer, "")
        # Eliminar cadenas '\\n', saltos de línea reales y espacios en blanco
        body = body.replace("\\n", "").replace("\n", "").replace("\r", "").replace(" ", "").strip()
        # Reconstruir la clave en formato PEM válido
        return f"{header}\n{body}\n{footer}\n"
    
    return key.replace("\\n", "\n")

def get_gspread_client():
    """Conecta a Google Sheets sanitizando automáticamente la clave privada."""
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    if "private_key" in creds_dict:
        creds_dict["private_key"] = fix_pem_key(creds_dict["private_key"])
        
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(credentials)

def append_to_sheets(sheet_id: str, datos_charla: dict, participantes: list):
    """Agrega una fila por cada participante en la hoja de Google Sheets."""
    client = get_gspread_client()
    sheet = client.open_by_key(sheet_id).sheet1
    
    filas_a_insertar = []
    for p in participantes:
        fila = [
            datos_charla.get("fecha"),
            datos_charla.get("tipo_actividad"),
            datos_charla.get("modalidad"),
            datos_charla.get("ubicacion"),
            datos_charla.get("relator_nombre"),
            datos_charla.get("relator_rut"),
            datos_charla.get("tema"),
            p.get("nombre"),
            p.get("rut"),
            p.get("cargo"),
            p.get("proyecto"),
            "FIRMADO" if p.get("firmado") else "PENDIENTE"
        ]
        filas_a_insertar.append(fila)
        
    sheet.append_rows(filas_a_insertar)
