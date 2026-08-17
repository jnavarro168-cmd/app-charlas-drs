import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

def fix_private_key(key: str) -> str:
    """
    Sana la clave privada PEM: repara saltos de línea, calcula y añade
    el relleno Base64 ('=') faltante y divide el cuerpo en bloques de 64 caracteres.
    """
    if not key:
        return key

    # Convertir saltos de línea escapados en saltos reales
    key = key.replace("\\n", "\n").strip()

    header = "-----BEGIN PRIVATE KEY-----"
    footer = "-----END PRIVATE KEY-----"

    if header in key and footer in key:
        # Extraer únicamente el cuerpo Base64
        body = key.split(header)[1].split(footer)[0]
        # Eliminar cualquier espacio, salto de línea o carácter invisible
        body = "".join(body.split())

        # Reparar el relleno Base64 (debe ser múltiplo de 4)
        missing_padding = len(body) % 4
        if missing_padding:
            body += "=" * (4 - missing_padding)

        # Dividir el cuerpo Base64 en líneas de 64 caracteres (estándar PEM)
        chunks = [body[i:i+64] for i in range(0, len(body), 64)]
        pem_body = "\n".join(chunks)

        return f"{header}\n{pem_body}\n{footer}\n"

    return key

def get_gspread_client():
    """Obtiene el cliente de Google Sheets con la clave sanitizada."""
    creds_dict = dict(st.secrets["gcp_service_account"])

    if "private_key" in creds_dict:
        creds_dict["private_key"] = fix_private_key(creds_dict["private_key"])

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(credentials)

def append_to_sheets(sheet_id: str, datos_charla: dict, participantes: list):
    """Agrega una fila por cada participante a la hoja de cálculo."""
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
