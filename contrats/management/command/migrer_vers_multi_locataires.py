# contrats/management/commands/migrer_vers_multi_locataires.py

from django.core.management.base import BaseCommand
from contrats.models import Contrats, ContratLocataire


class Command(BaseCommand):
    help = 'Migre les contrats existants vers le système multi-locataires'

    def handle(self, *args, **kwargs):
        contrats = Contrats.objects.filter(locataire__isnull=False)
        migres = 0
        erreurs = 0

        for contrat in contrats:
            try:
                # Vérifier si la migration n'a pas déjà eu lieu
                if not ContratLocataire.objects.filter(
                        contrat=contrat,
                        locataire=contrat.locataire
                ).exists():
                    # Créer la relation
                    ContratLocataire.objects.create(
                        contrat=contrat,
                        locataire=contrat.locataire,
                        principal=True,
                        ordre=1,
                        date_entree=contrat.date_debut,
                        role='titulaire'
                    )
                    migres += 1
                    self.stdout.write(f'✓ Contrat #{contrat.id} migré')
            except Exception as e:
                erreurs += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Erreur contrat #{contrat.id}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nMigration terminée : {migres} contrats migrés, {erreurs} erreurs'
            )
        )