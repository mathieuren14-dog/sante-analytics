import pandas as pd
import json
from pathlib import Path
from datetime import datetime


def charger_raw():
    """
    Charge les données brutes JSON sauvegardées par le collector.
    """
    chemin = Path("data/raw/withings/mesures.json")
    with open(chemin, "r") as f:
        data = json.load(f)
    return data


def transformer(data):
    """
    Convertit le format Withings encodé en DataFrame propre et enrichi.
    """
    type_map = {
        1: "poids_kg",
        4: "taille_m",
        5: "masse_sans_graisse_kg",
        6: "masse_grasse_pct",
        8: "masse_grasse_kg",
        76: "masse_musculaire_kg",
        77: "masse_hydrique_kg",
        88: "masse_osseuse_kg",
        170: "graisse_viscerale",
        226: "metabolisme_base_kcal",
        227: "age_metabolique",
        123: "vo2max"
    }

    lignes = []

    for groupe in data:
        date = datetime.fromtimestamp(groupe["date"])
        ligne = {"date": date.date(), "datetime": date}

        for mesure in groupe["measures"]:
            type_id = mesure["type"]
            if type_id in type_map:
                valeur = mesure["value"] * (10 ** mesure["unit"])
                ligne[type_map[type_id]] = round(valeur, 2)

        lignes.append(ligne)

    df = pd.DataFrame(lignes)

    # --- Dates ---
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["annee"] = df["datetime"].dt.year
    df["mois"] = df["datetime"].dt.month
    df["semaine"] = df["datetime"].dt.isocalendar().week.astype(int)
    df["jour_semaine"] = df["datetime"].dt.day_name()
    df["heure"] = df["datetime"].dt.hour

    # --- IMC ---
    TAILLE_M = 1.70
    if "poids_kg" in df.columns:
        df["imc"] = (df["poids_kg"] / (TAILLE_M ** 2)).round(1)

    # --- Masse sèche ---
    if "poids_kg" in df.columns and "masse_grasse_kg" in df.columns:
        df["masse_seche_kg"] = (df["poids_kg"] - df["masse_grasse_kg"]).round(2)

    # Trier par date
    df = df.sort_values("datetime", ascending=False).reset_index(drop=True)

    return df


def sauvegarder(df):
    """
    Sauvegarde en Parquet.
    """
    chemin = Path("data/clean/withings_mesures.parquet")
    chemin.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(chemin, index=False)
    print(f"✓ {len(df)} mesures sauvegardées dans {chemin}")


if __name__ == "__main__":
    print("Chargement des données brutes...")
    data = charger_raw()

    print("Transformation en cours...")
    df = transformer(data)

    print(f"\nAperçu :")
    print(df[["date", "poids_kg", "masse_grasse_pct",
              "masse_grasse_kg", "masse_musculaire_kg",
              "imc", "masse_seche_kg"]].head(10))

    print(f"\nColonnes : {df.columns.tolist()}")
    print(f"Dimensions : {df.shape}")

    sauvegarder(df)