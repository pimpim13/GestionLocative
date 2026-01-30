from django.core.management.base import BaseCommand
from paiements.models import TypeDepense


class Command(BaseCommand):
    help = 'Crée les types de dépenses par défaut'

    def handle(self, *args, **options):
        types = [
            {
                'nom': 'Entretien chaudière',
                'categorie': 'entretien',
                'recurrent': True,
                'deductible_fiscalement': True
            },
            {
                'nom': 'Eau parties communes',
                'categorie': 'charges',
                'recurrent': True,
                'deductible_fiscalement': True
            },
            {
                'nom': 'Électricité parties communes',
                'categorie': 'charges',
                'recurrent': True,
                'deductible_fiscalement': True
            },
            {
                'nom': 'Taxe foncière',
                'categorie': 'taxe',
                'recurrent': True,
                'deductible_fiscalement': True
            },
            {
                'nom': 'Assurance PNO',
                'categorie': 'assurance',
                'recurrent': True,
                'deductible_fiscalement': True
            },
            {
                'nom': 'Travaux de peinture',
                'categorie': 'travaux',
                'recurrent': False,
                'deductible_fiscalement': True
            },
        ]

        for type_data in types:
            TypeDepense.objects.get_or_create(**type_data)

        self.stdout.write(self.style.SUCCESS('Types de dépenses créés avec succès'))