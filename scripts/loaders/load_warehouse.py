import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/warehouse/sante.duckdb")


def connecter():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(DB_PATH))
    return conn


def charger_table(conn, nom_table, chemin_parquet):
    """
    Charge un fichier Parquet dans DuckDB.
    """
    chemin = Path(chemin_parquet)

    if not chemin.exists():
        print(f"⚠️ {chemin} non trouvé — lance d'abord le transformer")
        return

    conn.execute(f"""
        CREATE OR REPLACE TABLE {nom_table} AS
        SELECT * FROM read_parquet(?)
    """, [str(chemin)])

    count = conn.execute(f"SELECT COUNT(*) FROM {nom_table}").fetchone()[0]
    print(f"✓ {nom_table} chargée — {count} entrées")


def verifier_warehouse(conn):
    tables = conn.execute("SHOW TABLES").df()
    print(f"\nTables dans le warehouse :")
    print(tables)


if __name__ == "__main__":
    print("Connexion au warehouse...")
    conn = connecter()
    print(f"✓ Connecté à {DB_PATH}")

    print("\nChargement des tables...")
    charger_table(conn, "strava_activites",  "data/clean/strava_activites.parquet")
    charger_table(conn, "withings_mesures",  "data/clean/withings_mesures.parquet")
    charger_table(conn, "bien_etre",         "data/clean/bien_etre.parquet")
    charger_table(conn, "supplements",       "data/clean/supplements.parquet")
    charger_table(conn, "fatsecret_entrees",      "data/clean/fatsecret_entrees.parquet")
    charger_table(conn, "fatsecret_macros_repas", "data/clean/fatsecret_macros_repas.parquet")
    charger_table(conn, "fatsecret_macros_jour",  "data/clean/fatsecret_macros_jour.parquet")
    charger_table(conn, "nova_correspondance", "data/clean/nova_correspondance.parquet")
    charger_table(conn, "nova_par_jour",       "data/clean/nova_par_jour.parquet")
    verifier_warehouse(conn)

    conn.close()
    print("\n✓ Warehouse mis à jour")