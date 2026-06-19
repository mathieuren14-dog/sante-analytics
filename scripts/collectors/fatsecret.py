import os
import requests
import time
import hmac
import hashlib
import urllib.parse
import random
import string
import base64
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CONSUMER_KEY = os.getenv('FATSECRET_CLIENT_ID')
CONSUMER_SECRET = os.getenv('FATSECRET_CONSUMER_SECRET')
ACCESS_TOKEN = os.getenv('FATSECRET_ACCESS_TOKEN')
ACCESS_SECRET = os.getenv('FATSECRET_ACCESS_SECRET')

BASE_URL = 'https://platform.fatsecret.com/rest/server.api'


def generate_nonce():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))


def sign(method, url, params, consumer_secret, token_secret=''):
    sorted_params = '&'.join([
        f'{urllib.parse.quote(str(k), safe="")}={urllib.parse.quote(str(v), safe="")}'
        for k, v in sorted(params.items())
    ])
    base = f'{method}&{urllib.parse.quote(url, safe="")}&{urllib.parse.quote(sorted_params, safe="")}'
    key = f'{urllib.parse.quote(consumer_secret, safe="")}&{urllib.parse.quote(token_secret, safe="")}'
    return base64.b64encode(hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()).decode()


def appel_api(method_name, params_extra={}):
    params = {
        'method': method_name,
        'oauth_consumer_key': CONSUMER_KEY,
        'oauth_token': ACCESS_TOKEN,
        'oauth_nonce': generate_nonce(),
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time.time())),
        'oauth_version': '1.0',
        'format': 'json',
        **params_extra
    }
    params['oauth_signature'] = sign('POST', BASE_URL, params, CONSUMER_SECRET, ACCESS_SECRET)
    response = requests.post(BASE_URL, data=params)
    response.raise_for_status()
    return response.json()


def get_journal_du_jour():
    today = int(time.time() // 86400)
    return appel_api('food_entries.get.v2', {'date': str(today)})


def charger_historique():
    """
    Charge le fichier JSON historique existant.
    Retourne une liste vide si le fichier n'existe pas.
    """
    chemin = Path('data/raw/fatsecret/journal_historique.json')
    if chemin.exists():
        with open(chemin, 'r') as f:
            return json.load(f)
    return []


def sauvegarder_historique(entrees):
    """
    Sauvegarde toutes les entrées dans le fichier historique.
    """
    chemin = Path('data/raw/fatsecret/journal_historique.json')
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, 'w') as f:
        json.dump(entrees, f, indent=2)
    print(f'✓ {len(entrees)} entrées totales dans {chemin}')


def appender_journee(historique, nouvelles_entrees):
    """
    Ajoute les nouvelles entrées du jour à l'historique.
    Évite les doublons par food_entry_id.
    """
    ids_existants = {e['food_entry_id'] for e in historique}
    ajouts = 0

    for entree in nouvelles_entrees:
        if entree['food_entry_id'] not in ids_existants:
            historique.append(entree)
            ids_existants.add(entree['food_entry_id'])
            ajouts += 1

    print(f'✓ {ajouts} nouvelles entrées ajoutées')
    return historique


if __name__ == '__main__':
    print('Connexion à FatSecret...')

    print('\nRécupération du journal du jour...')
    journal_jour = get_journal_du_jour()
    food_entries = journal_jour.get('food_entries') if journal_jour else None
    entrees_jour = food_entries.get('food_entry', []) if food_entries else []

    if not entrees_jour:
        print('Aucune entrée pour aujourd\'hui — pipeline terminé')
    else:
        print(f'✓ {len(entrees_jour)} entrées récupérées')
        historique = charger_historique()
        historique = appender_journee(historique, entrees_jour)
        sauvegarder_historique(historique)