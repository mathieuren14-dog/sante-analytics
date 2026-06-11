import pandas as pd
import json
from pathlib import Path

def charger_raw():
    """
    Charge les données brutes JSON sauvegardées par le collector.
    """
    chemin = Path("data/raw/strava/activites.json")
    with open(chemin, "r") as f:
        activites = json.load(f)
    return activites


def transformer(activites):
    """
    Transforme les données brutes en DataFrame propre et enrichi.
    """
    df = pd.json_normalize(activites)

    # Colonnes utiles
    colonnes = [
        "id", "name", "type", "sport_type","workout_type",
        "start_date_local", "distance", "moving_time",
        "elapsed_time", "total_elevation_gain","elev_low","elev_high",
        "average_speed", "max_speed",
        "average_heartrate", "max_heartrate","has_heartrate",
        "average_watts", "suffer_score",
        "kudos_count", "achievement_count","location_city","location_country","gear_id"
    ]

    colonnes_existantes = [c for c in colonnes if c in df.columns]
    df = df[colonnes_existantes].copy()

       # --- Dates ---
    df["start_date_local"] = pd.to_datetime(df["start_date_local"])
    df["date"] = df["start_date_local"].dt.date
    df["annee"] = df["start_date_local"].dt.year
    df["mois"] = df["start_date_local"].dt.month
    df["semaine"] = df["start_date_local"].dt.isocalendar().week.astype(int)
    df["jour_semaine"] = df["start_date_local"].dt.day_name()
    df["heure"] = df["start_date_local"].dt.hour

    # --- Distance ---
    df["distance_km"] = (df["distance"] / 1000).round(2)

    # --- Temps ---
    df["moving_time_min"] = (df["moving_time"] / 60).round(1)
    df["moving_time_h"] = (df["moving_time"] / 3600).round(2)

    # --- Allure (min/km) — utile pour la course ---
    df["allure_min_km"] = (df["moving_time"] / 60 / df["distance_km"]).round(2)

    # --- Vitesse en km/h ---
    df["vitesse_kmh"] = (df["average_speed"] * 3.6).round(2)

    # --- Catégorie d'activité ---
    def categoriser(sport_type):
        course = ["Run", "TrailRun", "VirtualRun"]
        velo = ["Ride", "VirtualRide", "MountainBikeRide", "GravelRide"]
        natation = ["Swim"]
        marche = ["Walk", "Hike"]
        if sport_type in course:
            return "Course"
        elif sport_type in velo:
            return "Vélo"
        elif sport_type in natation:
            return "Natation"
        elif sport_type in marche:
            return "Marche/Randonnée"
        else:
            return "Autre"

    df["categorie"] = df["sport_type"].apply(categoriser)

    # --- Zones de FC (si disponible) ---
    if "average_heartrate" in df.columns:
        def zone_fc(fc):
            if pd.isna(fc):
                return "N/A"
            elif fc < 120:
                return "Z1 - Récupération"
            elif fc < 145:
                return "Z2 - Aérobie"
            elif fc < 160:
                return "Z3 - Tempo"
            elif fc < 175:
                return "Z4 - Seuil"
            else:
                return "Z5 - VO2max"

        df["zone_fc"] = df["average_heartrate"].apply(zone_fc)

    # Trier par date
    df = df.sort_values("start_date_local", ascending=False).reset_index(drop=True)

    return df


def sauvegarder(df):
    """
    Sauvegarde en Parquet — format optimal pour DuckDB et Power BI.
    """
    chemin = Path("data/clean/strava_activites.parquet")
    chemin.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(chemin, index=False)
    print(f"✓ {len(df)} activités sauvegardées dans {chemin}")


if __name__ == "__main__":
    print("Chargement des données brutes...")
    activites = charger_raw()

    print("Transformation en cours...")
    df = transformer(activites)

    print(f"\nAperçu :")
    print(df[["date", "sport_type", "categorie", "distance_km",
              "moving_time_min", "zone_fc" if "zone_fc" in df.columns
              else "vitesse_kmh"]].head(10))

    print(f"\nCatégories d'activités :")
    print(df["categorie"].value_counts())

    if "zone_fc" in df.columns:
        print(f"\nDistribution zones FC :")
        print(df["zone_fc"].value_counts())

    sauvegarder(df)