import subprocess
import sys

collectors = [
    "scripts/collectors/fatsecret.py",
    "scripts/collectors/garmin.py",
    "scripts/collectors/google_sheets.py",
    "scripts/collectors/strava.py",
    "scripts/collectors/withings.py",
]

transformers = [
    "scripts/transformers/nova_classification.py",
    "scripts/transformers/transform_fatsecret.py",
    "scripts/transformers/transform_garmin.py",
    "scripts/transformers/transform_google_sheets.py",
    "scripts/transformers/transform_strava.py",
    "scripts/transformers/transform_withings.py",
    "scripts/transformers/transform_nova.py",
]

loaders = [
    "scripts/loaders/load_warehouse.py",
]

def execute(scripts, etape):
    print(f"\n{'='*60}")
    print(f"ÉTAPE : {etape}")
    print(f"{'='*60}")

    for script in scripts:
        print(f"\n▶ {script}")

        resultat = subprocess.run(
            [sys.executable, script]
        )

        if resultat.returncode != 0:
            print(f"\n❌ Erreur dans {script}")
            sys.exit(1)

    print(f"\n✅ {etape} terminé")

if __name__ == "__main__":
    execute(collectors, "COLLECTE")
    execute(transformers, "TRANSFORMATION")
    execute(loaders, "CHARGEMENT")

    print("\n🎉 Pipeline complet terminé")