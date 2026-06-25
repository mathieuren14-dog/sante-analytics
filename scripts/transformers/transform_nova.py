import pandas as pd
import duckdb
from pathlib import Path


def charger_donnees():
    """
    Charge fatsecret_entrees et nova_correspondance.
    """
    conn = duckdb.connect()

    df_entrees = conn.execute("""
        SELECT *
        FROM read_parquet('data/clean/fatsecret_entrees.parquet')
    """).df()

    df_nova = conn.execute("""
        SELECT food_id, nova_group
        FROM read_parquet('data/clean/nova_correspondance.parquet')
        WHERE nova_group IS NOT NULL
    """).df()

    conn.close()

    print(f"✓ {len(df_entrees)} entrées FatSecret chargées")
    print(f"✓ {len(df_nova)} correspondances NOVA chargées")

    return df_entrees, df_nova


def calculer_nova_par_jour(df_entrees, df_nova):
    """
    JOIN fatsecret_entrees + nova_correspondance
    Calcule le % de calories par groupe NOVA par jour.
    """
    # Assurer les types
    df_entrees['food_id'] = df_entrees['food_id'].astype(str)
    df_nova['food_id'] = df_nova['food_id'].astype(str)

    # JOIN
    df = df_entrees.merge(df_nova, on='food_id', how='left')

    # Calories par groupe NOVA par jour
    df_jour = df.groupby(['date', 'annee', 'mois', 'semaine', 'jour_semaine']).apply(
        lambda g: pd.Series({
            'calories_totales': g['calories'].sum(),
            'cal_nova1': g.loc[g['nova_group'] == 1, 'calories'].sum(),
            'cal_nova2': g.loc[g['nova_group'] == 2, 'calories'].sum(),
            'cal_nova3': g.loc[g['nova_group'] == 3, 'calories'].sum(),
            'cal_nova4': g.loc[g['nova_group'] == 4, 'calories'].sum(),
            'cal_non_classifie': g.loc[g['nova_group'].isna(), 'calories'].sum(),
        })
    ).reset_index()

    # % calories par groupe
    total = df_jour['calories_totales'].replace(0, 1)  # éviter division par 0
    df_jour['nova1_pct'] = (df_jour['cal_nova1'] / total * 100).round(1)
    df_jour['nova2_pct'] = (df_jour['cal_nova2'] / total * 100).round(1)
    df_jour['nova3_pct'] = (df_jour['cal_nova3'] / total * 100).round(1)
    df_jour['nova4_pct'] = (df_jour['cal_nova4'] / total * 100).round(1)
    df_jour['non_classifie_pct'] = (df_jour['cal_non_classifie'] / total * 100).round(1)

    df_jour = df_jour.sort_values('date', ascending=False).reset_index(drop=True)

    return df_jour


def sauvegarder(df):
    chemin = Path("data/clean/nova_par_jour.parquet")
    chemin.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(chemin, index=False)
    print(f"✓ {len(df)} journées sauvegardées dans {chemin}")


if __name__ == '__main__':
    print("Chargement des données...")
    df_entrees, df_nova = charger_donnees()

    print("\nCalcul NOVA par jour...")
    df_nova_jour = calculer_nova_par_jour(df_entrees, df_nova)

    print(f"\nAperçu :")
    print(df_nova_jour[['date', 'calories_totales', 'cal_nova1',
                         'cal_nova4', 'nova1_pct', 'nova4_pct']].to_string())

    sauvegarder(df_nova_jour)