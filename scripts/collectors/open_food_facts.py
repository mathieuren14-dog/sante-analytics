import duckdb
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def collecter_et_sauvegarder():
    chemin_sortie = Path("data/raw/open_food_facts/off_nova.parquet")
    chemin_sortie.parent.mkdir(parents=True, exist_ok=True)

    token = os.getenv("HUGGINGFACE_TOKEN")

    print("Connexion à Hugging Face...")
    conn = duckdb.connect()

    conn.execute("INSTALL httpfs; LOAD httpfs;")
    conn.execute("SET unsafe_disable_etag_checks = true;")
    conn.execute(f"""
        CREATE SECRET hf_secret (
            TYPE HUGGINGFACE,
            TOKEN '{token}'
        )
    """)

    print("Requête en cours — filtrage Canada + USA + NOVA défini...")
    conn.execute(f"""
        COPY (
            SELECT
                code,
                nova_group,
                nutriscore_grade,
                brands,
                categories_tags,
                countries_tags,
                product_name
            FROM read_parquet('hf://datasets/openfoodfacts/product-database/food.parquet')
            WHERE nova_group IS NOT NULL
              AND lang = 'en'
              AND (
                  list_contains(countries_tags, 'en:canada') OR
                  list_contains(countries_tags, 'en:united-states')
              )
        ) TO '{chemin_sortie}' (FORMAT PARQUET)
    """)

    count = conn.execute(
        f"SELECT COUNT(*) FROM read_parquet('{chemin_sortie}')"
    ).fetchone()[0]

    print(f"✓ {count} produits sauvegardés dans {chemin_sortie}")
    conn.close()


if __name__ == '__main__':
    collecter_et_sauvegarder()