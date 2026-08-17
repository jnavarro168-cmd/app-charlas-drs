import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

def guardar_en_google_sheets(datos_registro):
    try:
        # Cargar credenciales desde la sección [gcp_service_account] de Secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        # Corregir la clave privada para evitar el error 'InvalidData(Invalid padding)'
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(credentials)
        
        # Abrir hoja de cálculo por ID
        sheet = client.open_by_key(st.secrets["GOOGLE_SHEETS_ID"]).sheet1
        sheet.append_row(datos_registro)
        
        return True, "Registro guardado correctamente en Google Sheets."
    except Exception as e:
        return False, f"Error al guardar en Google Sheets: {str(e)}"
