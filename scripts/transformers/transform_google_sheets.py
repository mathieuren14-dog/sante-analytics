import pandas as pd
from pathlib import Path


def charger_raw(nom):
    """
    Charge les données brutes CSV sauvegardées par le collector.
    """
    chemin = Path(f"data/raw/google_sheets/{nom}.csv")
    df = pd.read_csv(chemin)
    return df


def transformer_bien_etre(df):
    """
    Nettoie et enrichit les données de bien-être.
    """
    # Standardiser les noms de colonnes
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace('é', 'e')
        .str.replace('è', 'e')
        .str.replace('ê', 'e')
        .str.replace('à', 'a')
        .str.replace(' ', '_')
    )

    # Renommer si nécessaire
    rename_map = {
        'date': 'date',
        'moment': 'moment',
        'humeur': 'humeur',
        'energie': 'energie',
        'stress': 'stress',
        'sommeil_percu': 'sommeil_percu',
        'forme_musculaire': 'forme_musculaire',
        'notes': 'notes'
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Convertir la date
    df['date'] = pd.to_datetime(df['date'])

    # Dates
    df['annee'] = df['date'].dt.year
    df['mois'] = df['date'].dt.month
    df['semaine'] = df['date'].dt.isocalendar().week.astype(int)
    df['jour_semaine'] = df['date'].dt.day_name()

    # Standardiser moment
    df['moment'] = df['moment'].str.upper().str.strip()

    # Score bien-être global — moyenne des indicateurs
    colonnes_score = ['humeur', 'energie', 'stress', 'forme_musculaire']
    colonnes_existantes = [c for c in colonnes_score if c in df.columns]

    if colonnes_existantes:
        # Stress est inversé — 10 = très stressé, on inverse pour le score
        df_score = df[colonnes_existantes].copy()
        if 'stress' in df_score.columns:
            df_score['stress'] = 10 - df_score['stress']
        df['score_bien_etre'] = df_score.mean(axis=1).round(1)

    # Trier par date et moment
    df = df.sort_values(['date', 'moment'], ascending=[False, True]).reset_index(drop=True)

    return df


def transformer_supplements(df):
    """
    Nettoie et enrichit les données de suppléments.
    """
    # Standardiser les noms de colonnes
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace('é', 'e')
        .str.replace(' ', '_')
    )

    # Convertir la date
    df['date'] = pd.to_datetime(df['date'])

    # Dates
    df['annee'] = df['date'].dt.year
    df['mois'] = df['date'].dt.month
    df['semaine'] = df['date'].dt.isocalendar().week.astype(int)

    # Standardiser les champs texte
    df['supplement'] = df['supplement'].str.strip().str.upper()
    df['moment'] = df['moment'].str.strip().str.lower()
    df['pris'] = df['pris'].str.strip().str.lower()

    # Convertir pris en booléen
    df['pris'] = df['pris'].map({'oui': True, 'non': False, 'yes': True, 'no': False})

    # Trier par date
    df = df.sort_values('date', ascending=False).reset_index(drop=True)

    return df


def sauvegarder(df, nom):
    """
    Sauvegarde en Parquet.
    """
    chemin = Path(f"data/clean/{nom}.parquet")
    chemin.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(chemin, index=False)
    print(f"✓ {len(df)} entrées sauvegardées dans {chemin}")


if __name__ == "__main__":
    print("Chargement bien_etre...")
    df_bien_etre = charger_raw("bien_etre")
    df_bien_etre = transformer_bien_etre(df_bien_etre)
    print(f"\nAperçu bien_etre :")
    print(df_bien_etre)
    print(f"\nColonnes : {df_bien_etre.columns.tolist()}")
    sauvegarder(df_bien_etre, "bien_etre")

    print("\nChargement supplements...")
    df_supplements = charger_raw("supplements")
    df_supplements = transformer_supplements(df_supplements)
    print(f"\nAperçu supplements :")
    print(df_supplements)
    print(f"\nColonnes : {df_supplements.columns.tolist()}")
    sauvegarder(df_supplements, "supplements")