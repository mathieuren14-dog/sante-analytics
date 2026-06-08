import os
import requests
from dotenv import load_dotenv
import pandas as pd
import json
from pathlib import Path

# Charger les variables du .env
load_dotenv()

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

def get_access_token():
    """
    Utilise le refresh token pour obtenir un access token frais.
    Le access token expire après 6h — cette fonction le renouvelle automatiquement.
    """
    response = requests.post(
        url="https://www.strava.com/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
            "grant_type": "refresh_token"
        }
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_activites(access_token, nb_activites=200):
    """
    Récupère les activités Strava.
    Maximum 200 par page — on pagine automatiquement.
    """
    toutes_les_activites = []
    page = 1

    while True:
        response = requests.get(
            url="https://www.strava.com/api/v3/athlete/activities",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "per_page": 100,
                "page": page
            }
        )
        response.raise_for_status()
        activites = response.json()

        # Si page vide — on a tout récupéré
        if not activites:
            break

        toutes_les_activites.extend(activites)
        print(f"Page {page} — {len(activites)} activités récupérées")
        page += 1

    return toutes_les_activites


def sauvegarder_raw(activites):
    """
    Sauvegarde les données brutes en JSON — on ne modifie jamais les données brutes.
    """
    chemin = Path("data/raw/strava/activites.json")
    chemin.parent.mkdir(parents=True, exist_ok=True)

    with open(chemin, "w") as f:
        json.dump(activites, f, indent=2)

    print(f"✓ {len(activites)} activités sauvegardées dans {chemin}")


def activites_vers_dataframe(activites):
    """
    Convertit la liste d'activités en DataFrame pandas — prêt pour l'analyse.
    """
    df = pd.json_normalize(activites)

    # Garder seulement les colonnes utiles
    colonnes = [
        "id", "name", "type", "sport_type",
        "start_date_local", "distance", "moving_time",
        "elapsed_time", "total_elevation_gain",
        "average_speed", "max_speed",
        "average_heartrate", "max_heartrate",
        "average_watts", "suffer_score",
        "kudos_count", "achievement_count"
    ]

    # Garder seulement les colonnes qui existent
    colonnes_existantes = [c for c in colonnes if c in df.columns]
    df = df[colonnes_existantes]

    # Convertir la date
    df["start_date_local"] = pd.to_datetime(df["start_date_local"])

    # Convertir distance en km
    if "distance" in df.columns:
        df["distance_km"] = (df["distance"] / 1000).round(2)

    # Convertir temps en minutes
    if "moving_time" in df.columns:
        df["moving_time_min"] = (df["moving_time"] / 60).round(1)

    return df


if __name__ == "__main__":
    print("Connexion à Strava...")
    access_token = get_access_token()
    print("✓ Token obtenu")

    print("\nRécupération des activités...")
    activites = get_activites(access_token)

    print(f"\n✓ Total : {len(activites)} activités")

    # Sauvegarder les données brutes
    sauvegarder_raw(activites)

    # Convertir en DataFrame
    df = activites_vers_dataframe(activites)
    print(f"\nAperçu des données :")
    print(df.head())
    print(f"\nColonnes : {df.columns.tolist()}")
    print(f"Dimensions : {df.shape}")