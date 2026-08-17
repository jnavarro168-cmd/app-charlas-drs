import json
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
    # Carga el JSON guardado en Secrets
    raw_json = st.secrets["gcp_json_str"]
    creds_dict = json.loads(raw_json)
    return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

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
