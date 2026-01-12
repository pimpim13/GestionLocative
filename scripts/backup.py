# scripts/backup.py
"""
Script de sauvegarde et restauration de la base de données
Usage (depuis la RACINE du projet):
  - Backup: python scripts/backup.py --backup
  - Restore: python scripts/backup.py --restore backup_file.json
  - List: python scripts/backup.py --list
"""

import os
import sys
import django
import json
import argparse
from datetime import datetime
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
# Cela permet d'importer les modules Django correctement
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent  # Remonte d'un niveau (scripts -> racine)

# Ajouter le répertoire racine au sys.path si nécessaire
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')

try:
    django.setup()
except Exception as e:
    print(f"❌ Erreur lors de l'initialisation de Django: {e}")
    print(f"📁 Répertoire de travail: {os.getcwd()}")
    print(f"📁 Racine du projet: {PROJECT_ROOT}")
    print("\n💡 Assurez-vous d'exécuter le script depuis la racine du projet:")
    print(f"   cd {PROJECT_ROOT}")
    print(f"   python scripts/backup.py --backup")
    sys.exit(1)

from django.core import serializers
from django.apps import apps
from django.conf import settings


class DatabaseManager:
    """Gestionnaire de sauvegarde/restauration de la base de données"""

    def __init__(self):
        # Le dossier backups sera créé à la racine du projet
        self.backup_dir = PROJECT_ROOT / 'backups'
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, filename=None):
        """Crée une sauvegarde complète de la base de données"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'backup_{timestamp}.json'

        backup_path = self.backup_dir / filename

        print(f"📦 Création de la sauvegarde: {backup_path}")

        # Modèles à sauvegarder - selon votre diagramme
        models_to_backup = [
            'accounts.CustomUser',
            'immeuble.Immeuble',
            'immeuble.Appartement',
            'persons.Locataires',
            'persons.Proprietaires',
            'contrats.Contrats',
            'paiements.PaiementLocataire',
            'quittances.Quittance',
        ]

        all_objects = []
        stats = {}

        for model_name in models_to_backup:
            try:
                model = apps.get_model(model_name)
                objects = model.objects.all()
                count = objects.count()

                if count > 0:
                    serialized = serializers.serialize('json', objects)
                    model_data = json.loads(serialized)

                    for obj in model_data:
                        obj['model_name'] = model_name
                        all_objects.append(obj)

                stats[model_name] = count
                print(f"✅ {model._meta.verbose_name}: {count} objet(s)")

            except LookupError:
                print(f"⚠️  Modèle introuvable: {model_name} (ignoré)")
            except Exception as e:
                print(f"❌ Erreur avec {model_name}: {e}")

        # Sauvegarde dans le fichier
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'version': '1.0',
            'django_version': django.get_version(),
            'stats': stats,
            'objects': all_objects
        }

        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)

        file_size = backup_path.stat().st_size / 1024  # KB
        print(f"\n✅ Sauvegarde créée: {backup_path}")
        print(f"📊 Total: {len(all_objects)} objets sauvegardés")
        print(f"💾 Taille: {file_size:.1f} KB")

        return backup_path

    def restore_backup(self, backup_file):
        """Restaure une sauvegarde"""
        backup_path = Path(backup_file)

        if not backup_path.exists():
            backup_path = self.backup_dir / backup_file

        if not backup_path.exists():
            raise FileNotFoundError(f"Fichier de sauvegarde non trouvé: {backup_file}")

        print(f"📥 Restauration depuis: {backup_path}")

        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)

        print(f"📅 Sauvegarde du: {backup_data.get('timestamp', 'Inconnue')}")
        print(f"🔢 Django version: {backup_data.get('django_version', 'Inconnue')}")
        print(f"📊 Objets à restaurer: {len(backup_data['objects'])}")

        if 'stats' in backup_data:
            print("\n📋 Détail par modèle:")
            for model_name, count in backup_data['stats'].items():
                print(f"  - {model_name}: {count}")

        # Confirmation
        print("\n" + "=" * 60)
        response = input("⚠️  Cette opération va ÉCRASER les données existantes. Continuer? (y/N): ")
        if response.lower() != 'y':
            print("Restauration annulée.")
            return

        # Restauration par modèle
        restored_count = 0
        errors = []

        # Ordre de restauration (important pour les FK)
        restore_order = [
            'accounts.CustomUser',
            'persons.Proprietaires',
            'persons.Locataires',
            'immeuble.Immeuble',
            'immeuble.Appartement',
            'contrats.Contrats',
            'paiements.PaiementLocataire',
            'quittances.Quittance',
        ]

        # Grouper les objets par modèle
        objects_by_model = {}
        for obj_data in backup_data['objects']:
            model_name = obj_data.get('model_name')
            if model_name not in objects_by_model:
                objects_by_model[model_name] = []
            objects_by_model[model_name].append(obj_data)

        # Restaurer dans l'ordre
        for model_name in restore_order:
            if model_name not in objects_by_model:
                continue

            print(f"\n🔄 Restauration de {model_name}...")

            for obj_data in objects_by_model[model_name]:
                try:
                    model = apps.get_model(model_name)

                    # Nettoyage des données
                    obj_data_clean = {
                        'model': obj_data['model'],
                        'pk': obj_data['pk'],
                        'fields': obj_data['fields']
                    }

                    # Désérialisation
                    for deserialized_obj in serializers.deserialize('json', [obj_data_clean]):
                        deserialized_obj.save()
                        restored_count += 1

                except Exception as e:
                    error_msg = f"Erreur {model_name} (pk={obj_data.get('pk')}): {e}"
                    errors.append(error_msg)
                    print(f"  ⚠️  {error_msg}")

        print(f"\n{'=' * 60}")
        print(f"✅ Restauration terminée: {restored_count} objets restaurés")

        if errors:
            print(f"⚠️  {len(errors)} erreur(s) rencontrée(s)")
            print("\nDétail des erreurs:")
            for error in errors[:10]:  # Afficher max 10 erreurs
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... et {len(errors) - 10} autre(s) erreur(s)")

    def list_backups(self):
        """Liste les sauvegardes disponibles"""
        backups = list(self.backup_dir.glob('backup_*.json'))

        if not backups:
            print(f"Aucune sauvegarde trouvée dans: {self.backup_dir}")
            return

        print(f"📋 Sauvegardes disponibles dans: {self.backup_dir}\n")
        for backup in sorted(backups, reverse=True):
            size = backup.stat().st_size / 1024  # Taille en KB
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)

            # Lire les stats si disponibles
            try:
                with open(backup, 'r') as f:
                    data = json.load(f)
                    obj_count = len(data.get('objects', []))
                    print(f"  📦 {backup.name}")
                    print(f"     📅 {mtime.strftime('%d/%m/%Y %H:%M')}")
                    print(f"     💾 {size:.1f} KB - {obj_count} objets")
                    print()
            except:
                print(f"  📦 {backup.name} ({size:.1f} KB, {mtime.strftime('%d/%m/%Y %H:%M')})")


def main():
    parser = argparse.ArgumentParser(
        description='Gestionnaire de sauvegarde/restauration de la base de données',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation (depuis la racine du projet):
  python scripts/backup.py --backup
  python scripts/backup.py --backup --filename ma_sauvegarde.json
  python scripts/backup.py --list
  python scripts/backup.py --restore backup_20240108_153045.json
        """
    )

    parser.add_argument('--backup', action='store_true', help='Créer une sauvegarde')
    parser.add_argument('--restore', type=str, help='Restaurer depuis un fichier')
    parser.add_argument('--list', action='store_true', help='Lister les sauvegardes')
    parser.add_argument('--filename', type=str, help='Nom du fichier de sauvegarde')

    args = parser.parse_args()

    # Vérifier qu'on est bien à la racine du projet
    if not (PROJECT_ROOT / 'manage.py').exists():
        print("❌ Erreur: Le fichier manage.py n'a pas été trouvé.")
        print(f"📁 Répertoire actuel: {os.getcwd()}")
        print(f"📁 Racine détectée: {PROJECT_ROOT}")
        print("\n💡 Assurez-vous d'exécuter le script depuis la racine du projet:")
        print(f"   cd /chemin/vers/GestionLocative")
        print(f"   python scripts/backup.py --backup")
        sys.exit(1)

    db_manager = DatabaseManager()

    try:
        if args.backup:
            db_manager.create_backup(args.filename)
        elif args.restore:
            db_manager.restore_backup(args.restore)
        elif args.list:
            db_manager.list_backups()
        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n\n⚠️  Opération annulée par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()