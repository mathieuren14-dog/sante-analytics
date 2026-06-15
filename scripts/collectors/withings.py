import os
import requests
from dotenv import load_dotenv
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
import time

load_dotenv()

CLIENT_ID = os.getenv("WITHINGS_CLIENT_ID")
CLIENT_SECRET = os.getenv("WITHINGS_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("WITHINGS_REFRESH_TOKEN")


def get_access_token():
    """
    Utilise le refresh token pour obtenir un access token frais.
    """
    response = requests.post(
        url="https://wbsapi.withings.net/v2/oauth2",
        data={
            "action": "requesttoken",
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN
        }
    )
    response.raise_for_status()
    data = response.json()

    if data["status"] != 0:
        raise Exception(f"Erreur Withings : {data['error']}")

    return data["body"]["access_token"]


def get_mesures_corporelles(access_token):
    """
    Récupère les mesures corporelles — poids, masse grasse, IMC, etc.
    """
    response = requests.post(
        url="https://wbsapi.withings.net/measure",
        data={
            "action": "getmeas",
            "meastypes": "1,5,6,8,76,77,88",  # voir tableau ci-dessous
            "category": 1,  # 1 = mesures réelles (pas objectifs)
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    response.raise_for_status()
    data = response.json()

    if data["status"] != 0:
        raise Exception(f"Erreur mesures : {data}")

    return data["body"]["measuregrps"]


def parser_mesures(mesures_raw):
    """
    Convertit le format Withings (complexe) en DataFrame propre.

    Types de mesures Withings :
    1  = Poids (kg)
    5  = Masse grasse (%)
    6  = Masse grasse (kg)
    8  = Masse musculaire (kg)
    76 = Masse musculaire (%)
    77 = Masse hydrique (%)
    88 = Masse osseuse (kg)
    """
    type_map = {
        1: "poids_kg",
        5: "masse_grasse_pct",
        6: "masse_grasse_kg",
        8: "masse_musculaire_kg",
        76: "masse_musculaire_pct",
        77: "masse_hydrique_pct",
        88: "masse_osseuse_kg"
    }

    lignes = []

    for groupe in mesures_raw:
        date = datetime.fromtimestamp(groupe["date"])
        ligne = {"date": date.date(), "datetime": date}

        for mesure in groupe["measures"]:
            type_id = mesure["type"]
            if type_id in type_map:
                # Withings encode les valeurs avec un multiplicateur
                valeur = mesure["value"] * (10 ** mesure["unit"])
                ligne[type_map[type_id]] = round(valeur, 2)

        lignes.append(ligne)

    df = pd.DataFrame(lignes)
    df = df.sort_values("datetime", ascending=False).reset_index(drop=True)

    return df


def sauvegarder_raw(mesures_raw):
    """
    Sauvegarde les données brutes JSON.
    """
    chemin = Path("data/raw/withings/mesures.json")
    chemin.parent.mkdir(parents=True, exist_ok=True)

    with open(chemin, "w") as f:
        json.dump(mesures_raw, f, indent=2)

    print(f"✓ {len(mesures_raw)} groupes de mesures sauvegardés dans {chemin}")


if __name__ == "__main__":
    print("Connexion à Withings...")
    access_token = get_access_token()
    print("✓ Token obtenu")

    print("\nRécupération des mesures corporelles...")
    mesures_raw = get_mesures_corporelles(access_token)
    print(f"✓ {len(mesures_raw)} mesures récupérées")

    sauvegarder_raw(mesures_raw)

    print("\nParsing des mesures...")
    df = parser_mesures(mesures_raw)

    print(f"\nAperçu :")
    print(df.head(10))

    print(f"\nColonnes disponibles : {df.columns.tolist()}")
    print(f"Dimensions : {df.shape}")