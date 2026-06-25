import os
import json
from pathlib import Path
from datetime import date, timedelta
from dotenv import load_dotenv
from garminconnect import Garmin

load_dotenv()

EMAIL = os.getenv("GARMIN_EMAIL")
PASSWORD = os.getenv("GARMIN_PASSWORD")


def connecter():
    """
    Connexion à Garmin Connect.
    """
    client = Garmin(EMAIL, PASSWORD)
    client.login()
    print("✓ Connecté à Garmin Connect")
    return client


def get_sommeil(client, date_str):
    """
    Récupère les données de sommeil pour une date donnée.
    Format date : 'YYYY-MM-DD'
    """
    return client.get_sleep_data(date_str)


def get_hrv(client, date_str):
    """
    Récupère les données HRV pour une date donnée.
    """
    return client.get_hrv_data(date_str)


def get_body_battery(client, date_str):
    """
    Récupère le Body Battery pour une date donnée.
    """
    return client.get_body_battery(date_str)


def get_stress(client, date_str):
    """
    Récupère le score de stress pour une date donnée.
    """
    return client.get_stress_data(date_str)


def get_fc_repos(client, date_str):
    """
    Récupère la fréquence cardiaque au repos.
    """
    return client.get_rhr_day(date_str)


def get_spo2(client, date_str):
    """
    Récupère la saturation en oxygène.
    """
    return client.get_spo2_data(date_str)


def collecter_journee(client, date_str):
    """
    Collecte toutes les données Garmin pour une journée.
    """
    print(f"\n  Date : {date_str}")
    donnees = {'date': date_str}

    fonctions = [
        ('sommeil', get_sommeil),
        ('hrv', get_hrv),
        ('body_battery', get_body_battery),
        ('stress', get_stress),
        ('fc_repos', get_fc_repos),
        ('spo2', get_spo2),
    ]

    for nom, fonction in fonctions:
        try:
            donnees[nom] = fonction(client, date_str)
            print(f"    ✓ {nom}")
        except Exception as e:
            print(f"    ⚠️ {nom} — {e}")
            donnees[nom] = None

    return donnees


def sauvegarder_raw(donnees, nom):
    """
    Sauvegarde les données brutes JSON.
    """
    chemin = Path(f"data/raw/garmin/{nom}.json")
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, 'w') as f:
        json.dump(donnees, f, indent=2, default=str)
    print(f"\n✓ Données sauvegardées dans {chemin}")


if __name__ == '__main__':
    print("Connexion à Garmin...")
    client = connecter()

    # Charger l'historique existant
    chemin_historique = Path("data/raw/garmin/garmin_historique.json")
    if chemin_historique.exists():
        with open(chemin_historique, 'r') as f:
            historique = json.load(f)
        print(f"✓ {len(historique)} journées dans l'historique")
    else:
        historique = []

    # Dates des 7 derniers jours — toujours réévaluer
    dates_recentes = {
        (date.today() - timedelta(days=i)).strftime('%Y-%m-%d')
        for i in range(7)
    }

    # Retirer les 7 derniers jours de l'historique — on va les recollecteer
    historique = [d for d in historique if d['date'] not in dates_recentes]

    # Collecter les 7 derniers jours
    print("\nCollecte des 7 derniers jours...")
    for i in range(7):
        date_str = (date.today() - timedelta(days=i)).strftime('%Y-%m-%d')
        donnees = collecter_journee(client, date_str)
        historique.append(donnees)

    # Trier par date décroissante
    historique = sorted(historique, key=lambda x: x['date'], reverse=True)

    sauvegarder_raw(historique, 'garmin_historique')
    print(f"\n✓ Total : {len(historique)} journées dans l'historique")