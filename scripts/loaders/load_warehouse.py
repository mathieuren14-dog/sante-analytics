import duckdb
import pandas as pd
from pathlib import Path

# Chemin vers la base de données
DB_PATH = Path("data/warehouse/sante.duckdb")

def connecter():
    """
    Connexion à la base de données DuckDB persistante.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(DB_PATH))
    return conn


def charger_strava(conn):
    """
    Charge le Parquet Strava dans DuckDB.
    """
    chemin = Path("data/clean/strava_activites.parquet")

    if not chemin.exists():
        print("⚠️ Fichier Strava non trouvé — lance d'abord le transformer")
        return

    conn.execute("""
        CREATE OR REPLACE TABLE strava_activites AS
        SELECT * FROM read_parquet(?)
    """, [str(chemin)])

    count = conn.execute("SELECT COUNT(*) FROM strava_activites").fetchone()[0]
    print(f"✓ strava_activites chargée — {count} activités")


def verifier_warehouse(conn):
    """
    Affiche toutes les tables disponibles dans le warehouse.
    """
    tables = conn.execute("SHOW TABLES").df()
    print(f"\nTables dans le warehouse :")
    print(tables)


def apercu_strava(conn):
    """
    Aperçu rapide des données Strava dans DuckDB.
    """
    df = conn.execute("""
        SELECT
            categorie,
            COUNT(*) as nb_activites,
            ROUND(SUM(distance_km), 1) as distance_totale_km,
            ROUND(AVG(distance_km), 2) as distance_moyenne_km,
            ROUND(SUM(moving_time_h), 1) as heures_totales
        FROM strava_activites
        GROUP BY categorie
        ORDER BY nb_activites DESC
    """).df()

    print(f"\nRésumé par catégorie :")
    print(df)


if __name__ == "__main__":
    print("Connexion au warehouse...")
    conn = connecter()
    print(f"✓ Connecté à {DB_PATH}")

    print("\nChargement des données Strava...")
    charger_strava(conn)

    verifier_warehouse(conn)
    apercu_strava(conn)

    conn.close()
    print("\n✓ Warehouse mis à jour")