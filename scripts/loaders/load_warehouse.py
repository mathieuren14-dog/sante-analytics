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


def charger_withings(conn):
    """
    Charge le Parquet Withings dans DuckDB.
    """
    chemin = Path("data/clean/withings_mesures.parquet")

    if not chemin.exists():
        print("⚠️ Fichier Withings non trouvé — lance d'abord le transformer")
        return

    conn.execute("""
        CREATE OR REPLACE TABLE withings_mesures AS
        SELECT * FROM read_parquet(?)
    """, [str(chemin)])

    count = conn.execute("SELECT COUNT(*) FROM withings_mesures").fetchone()[0]
    print(f"✓ withings_mesures chargée — {count} mesures")


def verifier_warehouse(conn):
    """
    Affiche toutes les tables disponibles dans le warehouse.
    """
    tables = conn.execute("SHOW TABLES").df()
    print(f"\nTables dans le warehouse :")
    print(tables)


def apercu_withings(conn):
    """
    Aperçu rapide des données Withings dans DuckDB.
    """
    df = conn.execute("""
        SELECT
            date,
            poids_kg,
            masse_grasse_pct,
            masse_musculaire_kg,
            imc
        FROM withings_mesures
        WHERE poids_kg IS NOT NULL
        ORDER BY date DESC
        LIMIT 5
    """).df()

    print(f"\nDernières mesures Withings :")
    print(df)


if __name__ == "__main__":
    print("Connexion au warehouse...")
    conn = connecter()
    print(f"✓ Connecté à {DB_PATH}")

    print("\nChargement des données Strava...")
    charger_strava(conn)

    print("\nChargement des données Withings...")
    charger_withings(conn)

    verifier_warehouse(conn)
    apercu_withings(conn)

    conn.close()
    print("\n✓ Warehouse mis à jour")