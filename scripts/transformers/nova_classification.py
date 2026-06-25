import pandas as pd
import duckdb
import re
from pathlib import Path
from rapidfuzz import fuzz, process


def charger_open_food_facts():
    """
    Charge le Parquet Open Food Facts filtré.
    """
    chemin = Path("data/raw/open_food_facts/off_nova.parquet")
    conn = duckdb.connect()
    df = conn.execute(f"""
        SELECT
            code,
            nova_group,
            brands,
            product_name
        FROM read_parquet('{chemin}')
        WHERE nova_group IS NOT NULL
    """).df()
    conn.close()

    def extraire_nom(items):
        if items is None:
            return None
        try:
            lst = list(items)
            if not lst:
                return None
            for item in lst:
                if isinstance(item, dict) and item.get('text'):
                    return item.get('text')
        except Exception:
            return None
        return None

    df['product_name_en'] = df['product_name'].apply(extraire_nom)
    df = df.drop('product_name', axis=1)

    print(f"✓ {len(df)} produits Open Food Facts chargés")
    return df


def charger_aliments_fatsecret():
    """
    Charge les aliments uniques du journal FatSecret.
    """
    chemin = Path("data/clean/fatsecret_entrees.parquet")
    conn = duckdb.connect()
    df = conn.execute(f"""
        SELECT DISTINCT
            food_id,
            food_entry_name
        FROM read_parquet('{chemin}')
    """).df()
    conn.close()
    print(f"✓ {len(df)} aliments uniques FatSecret chargés")
    return df


def charger_nova_existante():
    """
    Charge la table nova_correspondance existante si elle existe.
    """
    chemin = Path("data/clean/nova_correspondance.parquet")
    if chemin.exists():
        conn = duckdb.connect()
        df = conn.execute(f"SELECT * FROM read_parquet('{chemin}')").df()
        conn.close()
        print(f"✓ {len(df)} entrées nova_correspondance existantes")
        return df
    return pd.DataFrame(columns=['food_id', 'food_name', 'nova_group', 'source'])


NOVA1_MOTS_CLES = [
    # Fruits
    'apple', 'banana', 'bananas', 'orange', 'oranges', 'mango', 'mangos',
    'pineapple', 'peach', 'peaches', 'pear', 'pears', 'grape', 'grapes',
    'blueberry', 'blueberries', 'strawberry', 'strawberries',
    'raspberry', 'raspberries', 'watermelon', 'avocado', 'avocados',
    'lemon', 'lemons', 'lime', 'limes', 'cherry', 'cherries',
    'melon', 'kiwi', 'pomegranate', 'fig', 'figs', 'plum', 'plums',
    'grapefruit', 'tangerine', 'clementine',

    # Légumes
    'spinach', 'broccoli', 'carrot', 'carrots', 'cucumber', 'cucumbers',
    'tomato', 'tomatoes', 'potato', 'potatoes', 'sweet potato', 'sweet potatoes',
    'asparagus', 'zucchini', 'kale', 'lettuce', 'celery',
    'onion', 'onions', 'garlic', 'mushroom', 'mushrooms',
    'pepper', 'peppers', 'beet', 'beets', 'cauliflower',
    'eggplant', 'artichoke', 'leek', 'leeks', 'radish',
    'cabbage', 'brussels sprout', 'brussels sprouts',

    # Protéines animales
    'egg', 'eggs', 'beef', 'salmon', 'tuna', 'shrimp', 'pork',
    'cod', 'tilapia', 'halibut', 'sardine', 'sardines',
    'horse meat', 'horsemeat',

    # Légumineuses et grains
    'oatmeal', 'oat', 'oats', 'rice', 'quinoa',
    'lentil', 'lentils', 'bean', 'beans',
    'chickpea', 'chickpeas', 'edamame',

    # Noix et graines non transformées
    'cashew', 'cashews', 'almond', 'almonds',
    'walnut', 'walnuts', 'pecan', 'pecans',
    'pistachio', 'pistachios',

    # Boissons naturelles
    'water', 'coffee', 'green tea', 'herbal tea', 'honey','maple syrup','extra virgin olive oil',
]

# Convertir en set lowercase pour lookup O(1)
NOVA1_SET = {mot.lower() for mot in NOVA1_MOTS_CLES}


def classifier_nova1(food_name):
    """
    Match exact insensible à la casse.
    Le nom FatSecret doit être exactement dans la liste NOVA 1.
    """
    return food_name.lower().strip() in NOVA1_SET


def fuzzy_match_nova(food_name, df_off, seuil=90):
    """
    Recherche fuzzy dans Open Food Facts.
    Insensible à la casse.
    """
    noms_off = df_off['product_name_en'].fillna('').str.lower().tolist()

    result = process.extractOne(
        food_name.lower(),
        noms_off,
        scorer=fuzz.token_set_ratio
    )

    if result and result[1] >= seuil:
        idx = result[2]
        nova_group = df_off.iloc[idx]['nova_group']
        score = result[1]
        return int(nova_group), f'open_food_facts_{score}'

    return None, None


def classifier_aliments(df_fatsecret, df_off, df_nova_existante):
    """
    Classifie les aliments FatSecret :
    1. Match exact NOVA 1
    2. Fuzzy match Open Food Facts
    3. Non classifié
    """
    ids_connus = set(df_nova_existante['food_id'].astype(str).tolist())
    nouvelles_lignes = []

    nouveaux = df_fatsecret[
        ~df_fatsecret['food_id'].astype(str).isin(ids_connus)
    ]

    print(f"\n{len(nouveaux)} nouveaux aliments à classifier...")

    for _, row in nouveaux.iterrows():
        food_id = str(row['food_id'])
        food_name = row['food_entry_name']

        # Étape 1 — Match exact NOVA 1
        if classifier_nova1(food_name):
            nova_group = 1
            source = 'mots_cles_nova1'

        # Étape 2 — Fuzzy match Open Food Facts
        else:
            nova_group, source = fuzzy_match_nova(food_name, df_off)

            # Étape 3 — Non classifié
            if nova_group is None:
                source = 'non_classifie'

        nouvelles_lignes.append({
            'food_id': food_id,
            'food_name': food_name,
            'nova_group': nova_group,
            'source': source
        })

        print(f"  {food_name} → NOVA {nova_group} ({source})")

    if nouvelles_lignes:
        df_nouvelles = pd.DataFrame(nouvelles_lignes)
        df_nova_complete = pd.concat(
            [df_nova_existante, df_nouvelles],
            ignore_index=True
        )
    else:
        df_nova_complete = df_nova_existante
        print("Aucun nouvel aliment à classifier")

    return df_nova_complete


def sauvegarder(df):
    chemin = Path("data/clean/nova_correspondance.parquet")
    chemin.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(chemin, index=False)
    print(f"\n✓ {len(df)} entrées sauvegardées dans {chemin}")


if __name__ == '__main__':
    print("Chargement des données...")
    df_off = charger_open_food_facts()
    df_fatsecret = charger_aliments_fatsecret()
    df_nova_existante = charger_nova_existante()

    print("\nClassification NOVA...")
    df_nova = classifier_aliments(df_fatsecret, df_off, df_nova_existante)

    print("\nRésultat :")
    print(df_nova.to_string())

    sauvegarder(df_nova)