import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import streamlit as st

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

def get_google_credentials():
    # Creamos una copia del diccionario de la cuenta de servicio
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # 1. Limpiamos comillas simples o dobles extra que hayan podido quedar al pegar
    pk = creds_dict["private_key"].strip()
    
    # 2. Convertimos los \n de texto a saltos de línea reales
    pk = pk.replace("\\n", "\n")
    
    # 3. Si por el formato TOML no tiene saltos de línea internos, los formateamos correctamente
    if "-----BEGIN PRIVATE KEY-----" in pk and "\n" not in pk.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", ""):
        body = pk.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "").strip()
        body_clean = body.replace(" ", "").replace("\n", "")
        # Dividir la clave en bloques de 64 caracteres como exige el estándar PEM
        lines = [body_clean[i:i+64] for i in range(0, len(body_clean), 64)]
        pk = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(lines) + "\n-----END PRIVATE KEY-----\n"

    creds_dict["private_key"] = pk

    return Credentials.from_service_account_info(
        creds_dict,
        scopes=SCOPES
    )

def append_to_sheets(spreadsheet_id: str, data: dict, participants: list):
    creds = get_google_credentials()
    client = gspread.authorize(creds)
    sheet = client.open_by_key(spreadsheet_id).sheet1

    rows_to_insert = []
    for p in participants:
        row = [
            data.get("fecha"),
            data.get("tipo_actividad"),
            data.get("modalidad"),
            data.get("relator_nombre"),
            data.get("relator_rut"),
            data.get("ubicacion"),
            data.get("tema"),
            p.get("nombre"),
            p.get("rut"),
            p.get("cargo"),
            p.get("proyecto"),
            "FIRMADO" if p.get("firmado") else "PENDIENTE"
        ]
        rows_to_insert.append(row)

    if rows_to_insert:
        sheet.append_rows(rows_to_insert)

def upload_pdf_to_drive(file_path: str, folder_id: str) -> str:
    creds = get_google_credentials()
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': file_path.split('/')[-1],
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='application/pdf')
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()

    return uploaded_file.get('webViewLink')
