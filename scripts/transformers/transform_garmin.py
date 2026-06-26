import pandas as pd
import json
from pathlib import Path
from datetime import datetime


def charger_raw():
    """
    Charge l'historique JSON Garmin.
    """
    chemin = Path("data/raw/garmin/garmin_historique.json")
    with open(chemin, "r") as f:
        data = json.load(f)
    print(f"✓ {len(data)} journées chargées")
    return data


def extraire_sommeil(jour):
    """
    Extrait les métriques de sommeil.
    """
    sommeil = jour.get('sommeil')
    if not sommeil:
        return {}

    dto = sommeil.get('dailySleepDTO', {})
    scores = dto.get('sleepScores', {})

    return {
        'sommeil_total_h': round(dto.get('sleepTimeSeconds', 0) / 3600, 2),
        'sommeil_profond_h': round(dto.get('deepSleepSeconds', 0) / 3600, 2),
        'sommeil_rem_h': round(dto.get('remSleepSeconds', 0) / 3600, 2),
        'sommeil_leger_h': round(dto.get('lightSleepSeconds', 0) / 3600, 2),
        'sommeil_eveille_h': round(dto.get('awakeSleepSeconds', 0) / 3600, 2),
        'eveils': dto.get('awakeCount'),
        'heure_coucher': dto.get('sleepStartTimestampLocal'),
        'heure_lever': dto.get('sleepEndTimestampLocal'),
        'respiration_moy': dto.get('averageRespirationValue'),
        'stress_sommeil': dto.get('avgSleepStress'),
        'sleep_score': scores.get('overall', {}).get('value') if isinstance(scores, dict) else None,
        'sleep_score_rem_pct': scores.get('remPercentage', {}).get('value') if isinstance(scores, dict) else None,
        'sleep_score_profond_pct': scores.get('deepPercentage', {}).get('value') if isinstance(scores, dict) else None,
        'sleep_score_stress': scores.get('stress', {}).get('qualifierKey') if isinstance(scores, dict) else None,
    }
    


def extraire_stress(jour):
    """
    Extrait les métriques de stress.
    """
    stress = jour.get('stress')
    if not stress:
        return {}

    return {
        'stress_max': stress.get('maxStressLevel'),
        'stress_moy': stress.get('avgStressLevel'),
    }


def extraire_fc_repos(jour):
    """
    Extrait la fréquence cardiaque au repos.
    """
    fc = jour.get('fc_repos')
    if not fc:
        return {}

    try:
        valeur = fc['allMetrics']['metricsMap']['WELLNESS_RESTING_HEART_RATE'][0]['value']
        return {'fc_repos': valeur}
    except Exception:
        return {'fc_repos': None}


def extraire_body_battery(jour):
    """
    Extrait les métriques Body Battery.
    """
    bb = jour.get('body_battery')
    if not bb or not isinstance(bb, list) or len(bb) == 0:
        return {}

    premier = bb[0]
    return {
        'body_battery_charge': premier.get('charged'),
        'body_battery_drain': premier.get('drained'),
    }


def extraire_spo2(jour):
    """
    Extrait les métriques SpO2.
    """
    spo2 = jour.get('spo2')
    if not spo2 or not isinstance(spo2, dict):
        return {}

    return {
        'spo2_moy': spo2.get('averageSpO2'),
        'spo2_min': spo2.get('lowestSpO2'),
        'spo2_sommeil': spo2.get('avgSleepSpO2'),
    }


def transformer(data):
    """
    Transforme toutes les journées en DataFrame propre.
    """
    lignes = []

    for jour in data:
        ligne = {'date': jour['date']}

        ligne.update(extraire_sommeil(jour))
        ligne.update(extraire_stress(jour))
        ligne.update(extraire_fc_repos(jour))
        ligne.update(extraire_body_battery(jour))
        ligne.update(extraire_spo2(jour))

        lignes.append(ligne)

    df = pd.DataFrame(lignes)

    # Convertir la date
    df['date'] = pd.to_datetime(df['date'])
    df['annee'] = df['date'].dt.year
    df['mois'] = df['date'].dt.month
    df['semaine'] = df['date'].dt.isocalendar().week.astype(int)
    df['jour_semaine'] = df['date'].dt.day_name()

    # Convertir heures coucher/lever
    for col in ['heure_coucher', 'heure_lever']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    df = df.sort_values('date', ascending=False).reset_index(drop=True)

    return df


def sauvegarder(df):
    """
    Sauvegarde en Parquet.
    """
    chemin = Path("data/clean/garmin_sante.parquet")
    chemin.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(chemin, index=False)
    print(f"✓ {len(df)} journées sauvegardées dans {chemin}")


if __name__ == '__main__':
    print("Chargement des données brutes...")
    data = charger_raw()

    print("\nTransformation en cours...")
    df = transformer(data)

    print(f"\nAperçu :")
    print(df[['date', 'sommeil_total_h', 'sommeil_profond_h',
              'sommeil_rem_h', 'fc_repos', 'stress_moy',
              'body_battery_charge', 'sleep_score']].to_string())

    print(f"\nColonnes : {df.columns.tolist()}")
    print(f"Dimensions : {df.shape}")

    sauvegarder(df)