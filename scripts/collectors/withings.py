import os
import requests
from dotenv import load_dotenv
import json
from pathlib import Path
import time

load_dotenv()

CLIENT_ID = os.getenv("WITHINGS_CLIENT_ID")
CLIENT_SECRET = os.getenv("WITHINGS_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("WITHINGS_REFRESH_TOKEN")


def get_access_token():
    """
    Utilise le refresh token pour obtenir un access token frais.
    Withings invalide le refresh token à chaque utilisation et en retourne un nouveau.
    On sauvegarde automatiquement le nouveau refresh token dans .env.
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

    # Withings retourne un nouveau refresh token à chaque appel
    # On le sauvegarde immédiatement dans .env
    nouveau_refresh_token = data["body"]["refresh_token"]
    mettre_a_jour_env("WITHINGS_REFRESH_TOKEN", nouveau_refresh_token)

    return data["body"]["access_token"]


def mettre_a_jour_env(cle, valeur):
    """
    Met à jour une valeur dans le fichier .env automatiquement.
    """
    env_path = Path(".env")
    contenu = env_path.read_text()

    lignes = contenu.split("\n")
    nouvelles_lignes = []

    for ligne in lignes:
        if ligne.startswith(f"{cle}="):
            nouvelles_lignes.append(f"{cle}={valeur}")
        else:
            nouvelles_lignes.append(ligne)

    env_path.write_text("\n".join(nouvelles_lignes))
    print(f"✓ Nouveau refresh token sauvegardé dans .env")


def get_mesures_corporelles(access_token):
    """
    Récupère toutes les mesures corporelles depuis le début.
    Types inclus :
    1   = Poids (kg)
    4   = Taille (m)
    5   = Masse sans graisse (kg)
    6   = Masse grasse (%)
    8   = Masse grasse (kg)
    76  = Masse musculaire (kg)
    77  = Hydratation (kg)
    88  = Masse osseuse (kg)
    123 = VO2 max
    170 = Graisse viscérale
    226 = Métabolisme de base (kcal)
    227 = Âge métabolique
    """
    response = requests.post(
        url="https://wbsapi.withings.net/measure",
        data={
            "action": "getmeas",
            "meastypes": "1,4,5,6,8,76,77,88,123,170,226,227",
            "category": 1,
            "startdate": 0,
            "enddate": int(time.time())
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    response.raise_for_status()
    data = response.json()

    if data["status"] != 0:
        raise Exception(f"Erreur mesures : {data}")

    return data["body"]["measuregrps"]


def sauvegarder_raw(mesures_raw):
    """
    Sauvegarde les données brutes JSON — on ne modifie jamais les données brutes.
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