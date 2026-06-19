import pandas as pd
import json
from pathlib import Path
from datetime import date, timedelta


def charger_raw():
    chemin = Path("data/raw/fatsecret/journal_historique.json")
    if not chemin.exists():
        print("⚠️ Aucun historique trouvé — lance d'abord le collector")
        return []
    with open(chemin, "r") as f:
        return json.load(f)


def convertir_date(date_int):
    return date(1970, 1, 1) + timedelta(days=int(date_int))


def transformer_entrees(entrees):
    """
    Table détaillée — une ligne par aliment par repas.
    Toutes les macros disponibles.
    """
    if not entrees:
        return pd.DataFrame()

    df = pd.DataFrame(entrees)

    # --- Convertir tous les champs numériques ---
    colonnes_numeriques = [
        'calories', 'carbohydrate', 'protein', 'fat',
        'saturated_fat', 'polyunsaturated_fat', 'monounsaturated_fat',
        'fiber', 'sugar', 'sodium', 'potassium', 'cholesterol',
        'vitamin_a', 'vitamin_c', 'calcium', 'iron', 'trans_fat',
        'number_of_units'
    ]
    for col in colonnes_numeriques:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # --- Convertir la date ---
    df['date'] = df['date_int'].apply(convertir_date)
    df['date'] = pd.to_datetime(df['date'])
    df['annee'] = df['date'].dt.year
    df['mois'] = df['date'].dt.month
    df['semaine'] = df['date'].dt.isocalendar().week.astype(int)
    df['jour_semaine'] = df['date'].dt.day_name()

    # --- Standardiser le repas ---
    df['meal'] = df['meal'].str.lower().str.strip()

    # --- Trier ---
    ordre_repas = {'breakfast': 0, 'lunch': 1, 'dinner': 2, 'other': 3}
    df['meal_ordre'] = df['meal'].map(ordre_repas).fillna(4)
    df = df.sort_values(['date', 'meal_ordre']).drop('meal_ordre', axis=1)
    df = df.reset_index(drop=True)

    return df


def agreger_par_repas(df):
    """
    Table par repas — totaux par date + type de repas.
    Permet d'analyser l'impact de chaque repas sur l'énergie et l'humeur.
    """
    if df.empty:
        return pd.DataFrame()

    colonnes_somme = [
        'calories', 'carbohydrate', 'protein', 'fat',
        'saturated_fat', 'polyunsaturated_fat', 'monounsaturated_fat',
        'fiber', 'sugar', 'sodium', 'potassium',
        'cholesterol', 'trans_fat'
    ]
    colonnes_existantes = [c for c in colonnes_somme if c in df.columns]

    df_repas = df.groupby(
        ['date', 'annee', 'mois', 'semaine', 'jour_semaine', 'meal']
    )[colonnes_existantes].sum().reset_index()

    df_repas = df_repas.sort_values(['date', 'meal']).reset_index(drop=True)

    return df_repas


def agreger_par_jour(df):
    """
    Table journalière — totaux complets par jour.
    Toutes les macros disponibles.
    """
    if df.empty:
        return pd.DataFrame()

    colonnes_somme = [
        'calories', 'carbohydrate', 'protein', 'fat',
        'saturated_fat', 'polyunsaturated_fat', 'monounsaturated_fat',
        'fiber', 'sugar', 'sodium', 'potassium',
        'cholesterol', 'trans_fat', 'vitamin_a', 'vitamin_c',
        'calcium', 'iron'
    ]
    colonnes_existantes = [c for c in colonnes_somme if c in df.columns]

    df_jour = df.groupby(
        ['date', 'annee', 'mois', 'semaine', 'jour_semaine']
    )[colonnes_existantes].sum().reset_index()

    df_jour = df_jour.sort_values('date', ascending=False).reset_index(drop=True)

    return df_jour


def sauvegarder(df, nom):
    chemin = Path(f"data/clean/{nom}.parquet")
    chemin.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(chemin, index=False)
    print(f"✓ {len(df)} entrées sauvegardées dans {chemin}")


if __name__ == "__main__":
    print("Chargement des données brutes...")
    entrees = charger_raw()
    print(f"✓ {len(entrees)} entrées chargées")

    print("\nTransformation des entrées détaillées...")
    df_entrees = transformer_entrees(entrees)

    if not df_entrees.empty:
        print(f"\nAperçu entrées détaillées :")
        print(df_entrees[['date', 'meal', 'food_entry_name',
                          'calories', 'protein', 'carbohydrate', 'fat']].head(10))
        sauvegarder(df_entrees, "fatsecret_entrees")

        print("\nAgrégation par repas...")
        df_repas = agreger_par_repas(df_entrees)
        print(f"\nAperçu macros par repas :")
        print(df_repas[['date', 'meal', 'calories',
                        'protein', 'carbohydrate', 'fat', 'fiber']].head(10))
        sauvegarder(df_repas, "fatsecret_macros_repas")

        print("\nAgrégation par jour...")
        df_jour = agreger_par_jour(df_entrees)
        print(f"\nAperçu macros par jour :")
        print(df_jour[['date', 'calories', 'protein',
                       'carbohydrate', 'fat', 'fiber', 'sodium']].head(10))
        sauvegarder(df_jour, "fatsecret_macros_jour")