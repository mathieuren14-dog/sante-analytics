import os
import pandas as pd
import json
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
import gspread

load_dotenv()

SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
CREDENTIALS_PATH = "credentials_google.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def connecter():
    """
    Connexion à Google Sheets via le compte de service.
    """
    creds = Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    print("✓ Connecté à Google Sheets")
    return sheet


def get_bien_etre(sheet):
    """
    Récupère les données de l'onglet bien_etre.
    """
    worksheet = sheet.worksheet("bien_etre")
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    print(f"✓ bien_etre — {len(df)} entrées récupérées")
    return df


def get_supplements(sheet):
    """
    Récupère les données de l'onglet supplements.
    """
    worksheet = sheet.worksheet("supplements")
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    print(f"✓ supplements — {len(df)} entrées récupérées")
    return df


def sauvegarder_raw(df, nom):
    """
    Sauvegarde les données brutes en CSV.
    """
    chemin = Path(f"data/raw/google_sheets/{nom}.csv")
    chemin.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(chemin, index=False)
    print(f"✓ {nom} sauvegardé dans {chemin}")


if __name__ == "__main__":
    print("Connexion à Google Sheets...")
    sheet = connecter()

    print("\nRécupération des données...")
    df_bien_etre = get_bien_etre(sheet)
    df_supplements = get_supplements(sheet)

    print("\nSauvegarde des données brutes...")
    sauvegarder_raw(df_bien_etre, "bien_etre")
    sauvegarder_raw(df_supplements, "supplements")

    print("\nAperçu bien_etre :")
    print(df_bien_etre.head())

    print("\nAperçu supplements :")
    print(df_supplements.head())