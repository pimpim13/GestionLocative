# contrats/tests.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta

from .models import Contrats, ContratLocataire
from persons.models import Locataires, Proprietaires
from immeuble.models import Immeuble, Appartement

User = get_user_model()


class ContratsModelTestCase(TestCase):
    """Tests pour le modèle Contrats"""

    def setUp(self):
        """Prépare les données pour les tests"""
        # Créer un propriétaire
        self.proprietaire = Proprietaires.objects.create(
            nom="Dupont",
            prenom="Jean",
            email="jean.dupont@example.com",
            telephone="0123456789"
        )

        # Créer un immeuble
        self.immeuble = Immeuble.objects.create(
            nom="Résidence Les Oliviers",
            adresse="123 Rue de la Paix",
            ville="Paris",
            code_postal="75001",
            charges_communes_annuelles=Decimal("5000.00")
        )

        # Créer un appartement
        self.appartement = Appartement.objects.create(
            immeuble=self.immeuble,
            numero="A101",
            proprietaire=self.proprietaire,
            etage=1,
            loyer_base=Decimal("800.00"),
            charges_mensuelles=Decimal("100.00")
        )

        # Créer des locataires
        self.locataire1 = Locataires.objects.create(
            nom="Martin",
            prenom="Alice",
            email="alice.martin@example.com",
            telephone="0612345678"
        )

        self.locataire2 = Locataires.objects.create(
            nom="Bernard",
            prenom="Bob",
            email="bob.bernard@example.com",
            telephone="0623456789"
        )

        # Créer un contrat
        self.contrat = Contrats.objects.create(
            appartement=self.appartement,
            date_debut=date(2024, 1, 1),
            date_fin=date(2025, 12, 31),
            loyer_mensuel=Decimal("800.00"),
            charges_mensuelles=Decimal("100.00"),
            depot_garantie=Decimal("1600.00"),
            jour_echeance=5
        )

    def test_contrat_creation(self):
        """Test la création d'un contrat"""
        self.assertEqual(self.contrat.appartement, self.appartement)
        self.assertEqual(self.contrat.loyer_mensuel, Decimal("800.00"))
        self.assertEqual(self.contrat.charges_mensuelles, Decimal("100.00"))
        self.assertTrue(self.contrat.actif)
        self.assertFalse(self.contrat.preavis_donne)

    def test_contrat_str(self):
        """Test la représentation string d'un contrat"""
        # Ajouter un locataire pour tester __str__
        self.contrat.ajouter_locataire(self.locataire1, principal=True)
        expected = f"Contrat {self.locataire1.nom_complet} - {self.appartement}"
        self.assertEqual(str(self.contrat), expected)

    def test_loyer_total_property(self):
        """Test le calcul du loyer total"""
        self.assertEqual(self.contrat.loyer_total, Decimal("900.00"))

    def test_loyer_total_avec_valeurs_nulles(self):
        """Test loyer_total avec valeurs NULL"""
        contrat = Contrats.objects.create(
            appartement=self.appartement,
            date_debut=date(2024, 1, 1),
            loyer_mensuel=None,
            charges_mensuelles=None
        )
        self.assertEqual(contrat.loyer_total, 0)

    def test_duree_mois_property(self):
        """Test le calcul de la durée en mois"""
        self.assertEqual(self.contrat.duree_mois, 24)

    def test_duree_mois_sans_date_fin(self):
        """Test durée en mois sans date de fin"""
        contrat = Contrats.objects.create(
            appartement=self.appartement,
            date_debut=date(2024, 1, 1),
            loyer_mensuel=Decimal("800.00")
        )
        self.assertIsNone(contrat.duree_mois)

    def test_jour_echeance_validation(self):
        """Test la validation du jour d'échéance"""
        with self.assertRaises(ValidationError):
            contrat = Contrats(
                appartement=self.appartement,
                date_debut=date(2024, 1, 1),
                jour_echeance=32  # Invalide
            )
            contrat.full_clean()

    def test_contrat_ordering(self):
        """Test l'ordre par défaut des contrats"""
        contrat2 = Contrats.objects.create(
            appartement=self.appartement,
            date_debut=date(2023, 1, 1),
            loyer_mensuel=Decimal("750.00")
        )
        contrats = list(Contrats.objects.all())
        # Le plus récent doit être en premier (ordre décroissant)
        self.assertEqual(contrats[0], self.contrat)
        self.assertEqual(contrats[1], contrat2)


class ContratLocataireModelTestCase(TestCase):
    """Tests pour le modèle ContratLocataire"""

    def setUp(self):
        """Prépare les données pour les tests"""
        # Créer les dépendances
        self.proprietaire = Proprietaires.objects.create(
            nom="Test",
            prenom="User",
            email="test@example.com",
            telephone="0123456789"
        )

        self.immeuble = Immeuble.objects.create(
            nom="Immeuble Test",
            adresse="Test Address",
            ville="Paris",
            code_postal="75001"
        )

        self.appartement = Appartement.objects.create(
            immeuble=self.immeuble,
            numero="101",
            proprietaire=self.proprietaire,
            etage=1
        )

        self.contrat = Contrats.objects.create(
            appartement=self.appartement,
            date_debut=date(2024, 1, 1),
            loyer_mensuel=Decimal("800.00")
        )

        self.locataire1 = Locataires.objects.create(
            nom="Doe",
            prenom="John",
            email="john.doe@example.com",
            telephone="0612345678"
        )

        self.locataire2 = Locataires.objects.create(
            nom="Smith",
            prenom="Jane",
            email="jane.smith@example.com",
            telephone="0623456789"
        )

    def test_ajouter_locataire(self):
        """Test l'ajout d'un locataire au contrat"""
        self.contrat.ajouter_locataire(self.locataire1, principal=True)

        self.assertEqual(self.contrat.locataires.count(), 1)
        relation = ContratLocataire.objects.get(contrat=self.contrat, locataire=self.locataire1)
        self.assertTrue(relation.principal)
        self.assertEqual(relation.ordre, 1)

    def test_ajouter_plusieurs_locataires(self):
        """Test l'ajout de plusieurs locataires"""
        self.contrat.ajouter_locataire(self.locataire1, principal=True)
        self.contrat.ajouter_locataire(self.locataire2, principal=False)

        self.assertEqual(self.contrat.locataires.count(), 2)

    def test_ordre_automatique(self):
        """Test que l'ordre s'incrémente automatiquement"""
        self.contrat.ajouter_locataire(self.locataire1)
        self.contrat.ajouter_locataire(self.locataire2)

        relation1 = ContratLocataire.objects.get(contrat=self.contrat, locataire=self.locataire1)
        relation2 = ContratLocataire.objects.get(contrat=self.contrat, locataire=self.locataire2)

        self.assertEqual(relation1.ordre, 1)
        self.assertEqual(relation2.ordre, 2)

    def test_get_locataire_principal(self):
        """Test la récupération du locataire principal"""
        self.contrat.ajouter_locataire(self.locataire1, principal=False)
        self.contrat.ajouter_locataire(self.locataire2, principal=True)

        principal = self.contrat.get_locataire_principal()
        self.assertEqual(principal, self.locataire2)

    def test_get_locataire_principal_fallback(self):
        """Test le fallback quand aucun principal défini"""
        self.contrat.ajouter_locataire(self.locataire1, principal=False)
        self.contrat.ajouter_locataire(self.locataire2, principal=False)

        principal = self.contrat.get_locataire_principal()
        # Doit retourner le premier par ordre
        self.assertEqual(principal, self.locataire1)

    def test_get_locataire_principal_aucun(self):
        """Test quand aucun locataire"""
        principal = self.contrat.get_locataire_principal()
        self.assertIsNone(principal)

    def test_get_tous_locataires(self):
        """Test la récupération de tous les locataires actifs"""
        self.contrat.ajouter_locataire(self.locataire1)
        self.contrat.ajouter_locataire(self.locataire2)

        locataires = self.contrat.get_tous_locataires()
        self.assertEqual(locataires.count(), 2)

    def test_get_tous_locataires_exclut_sortis(self):
        """Test que les locataires sortis sont exclus"""
        self.contrat.ajouter_locataire(self.locataire1)
        self.contrat.ajouter_locataire(self.locataire2)

        # Marquer un locataire comme sorti
        self.contrat.retirer_locataire(self.locataire2, date(2024, 6, 30))

        locataires = self.contrat.get_tous_locataires()
        self.assertEqual(locataires.count(), 1)
        self.assertEqual(locataires.first(), self.locataire1)

    def test_get_locataires_display_un_locataire(self):
        """Test l'affichage avec un seul locataire"""
        self.contrat.ajouter_locataire(self.locataire1)
        display = self.contrat.get_locataires_display()
        self.assertEqual(display, self.locataire1.nom_complet)

    def test_get_locataires_display_deux_locataires(self):
        """Test l'affichage avec deux locataires"""
        self.contrat.ajouter_locataire(self.locataire1)
        self.contrat.ajouter_locataire(self.locataire2)
        display = self.contrat.get_locataires_display()
        expected = f"{self.locataire1.nom_complet} et {self.locataire2.nom_complet}"
        self.assertEqual(display, expected)

    def test_get_locataires_display_trois_locataires(self):
        """Test l'affichage avec trois locataires"""
        locataire3 = Locataires.objects.create(
            nom="Johnson",
            prenom="Mike",
            email="mike@example.com",
            telephone="0634567890"
        )

        self.contrat.ajouter_locataire(self.locataire1)
        self.contrat.ajouter_locataire(self.locataire2)
        self.contrat.ajouter_locataire(locataire3)

        display = self.contrat.get_locataires_display()
        self.assertIn(self.locataire1.nom_complet, display)
        self.assertIn(self.locataire2.nom_complet, display)
        self.assertIn(locataire3.nom_complet, display)

    def test_get_locataires_display_aucun(self):
        """Test l'affichage sans locataire"""
        display = self.contrat.get_locataires_display()
        self.assertEqual(display, "Aucun locataire")

    def test_retirer_locataire(self):
        """Test le retrait d'un locataire"""
        self.contrat.ajouter_locataire(self.locataire1)
        date_sortie = date(2024, 6, 30)

        self.contrat.retirer_locataire(self.locataire1, date_sortie)

        relation = ContratLocataire.objects.get(contrat=self.contrat, locataire=self.locataire1)
        self.assertEqual(relation.date_sortie, date_sortie)
        self.assertFalse(relation.est_actif)

    def test_un_seul_principal_par_contrat(self):
        """Test qu'un seul locataire peut être principal"""
        self.contrat.ajouter_locataire(self.locataire1, principal=True)
        self.contrat.ajouter_locataire(self.locataire2, principal=False)

        # Définir le second comme principal
        relation2 = ContratLocataire.objects.get(contrat=self.contrat, locataire=self.locataire2)
        relation2.principal = True
        relation2.save()

        # Vérifier que le premier n'est plus principal
        relation1 = ContratLocataire.objects.get(contrat=self.contrat, locataire=self.locataire1)
        self.assertFalse(relation1.principal)
        self.assertTrue(relation2.principal)

    def test_contrat_locataire_unique_together(self):
        """Test la contrainte unique_together"""
        self.contrat.ajouter_locataire(self.locataire1)

        # Essayer d'ajouter le même locataire deux fois
        with self.assertRaises(Exception):
            ContratLocataire.objects.create(
                contrat=self.contrat,
                locataire=self.locataire1,
                date_entree=date(2024, 1, 1)
            )

    def test_est_actif_property(self):
        """Test la propriété est_actif"""
        self.contrat.ajouter_locataire(self.locataire1)
        relation = ContratLocataire.objects.get(contrat=self.contrat, locataire=self.locataire1)

        self.assertTrue(relation.est_actif)

        relation.date_sortie = date(2024, 6, 30)
        relation.save()

        self.assertFalse(relation.est_actif)


class ContratsViewsTestCase(TestCase):
    """Tests pour les vues de l'app contrats"""

    def setUp(self):
        """Prépare les données pour les tests"""
        self.client = Client()

        # Créer un utilisateur
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )

        # Créer les dépendances
        self.proprietaire = Proprietaires.objects.create(
            nom="Test",
            prenom="Owner",
            email="owner@example.com",
            telephone="0123456789"
        )

        self.immeuble = Immeuble.objects.create(
            nom="Test Building",
            adresse="123 Test St",
            ville="Paris",
            code_postal="75001"
        )

        self.appartement = Appartement.objects.create(
            immeuble=self.immeuble,
            numero="101",
            proprietaire=self.proprietaire,
            etage=1,
            loyer_base=Decimal("800.00")
        )

        self.locataire = Locataires.objects.create(
            nom="Test",
            prenom="Tenant",
            email="tenant@example.com",
            telephone="0612345678"
        )

        self.contrat = Contrats.objects.create(
            appartement=self.appartement,
            date_debut=date(2024, 1, 1),
            loyer_mensuel=Decimal("800.00"),
            charges_mensuelles=Decimal("100.00")
        )

    def test_contrats_list_view_requiert_login(self):
        """Test que la liste des contrats nécessite une authentification"""
        url = reverse('contrats:contrats_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirection vers login

    def test_contrats_list_view_avec_login(self):
        """Test l'accès à la liste des contrats avec authentification"""
        self.client.login(email="test@example.com", password="testpass123")
        url = reverse('contrats:contrats_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contrats/contrats_list.html')
        self.assertIn('contrats', response.context)

    def test_contrat_create_view_get(self):
        """Test l'affichage du formulaire de création"""
        self.client.login(email="test@example.com", password="testpass123")
        url = reverse('contrats:contrat_create')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contrats/contrat_create.html')

    def test_contrat_create_view_post(self):
        """Test la création d'un contrat via POST"""
        self.client.login(email="test@example.com", password="testpass123")
        url = reverse('contrats:contrat_create')

        data = {
            'appartement': self.appartement.id,
            'date_debut': '2024-06-01',
            'loyer_mensuel': '850.00',
            'charges_mensuelles': '120.00',
            'jour_echeance': 5,
            'actif': True
        }

        response = self.client.post(url, data)

        # Doit rediriger vers la gestion des locataires
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Contrats.objects.filter(loyer_mensuel=Decimal("850.00")).exists())

    def test_contrat_update_view(self):
        """Test la modification d'un contrat"""
        self.client.login(email="test@example.com", password="testpass123")
        url = reverse('contrats:contrat_update', kwargs={'pk': self.contrat.pk})

        data = {
            'appartement': self.appartement.id,
            'date_debut': '2024-01-01',
            'loyer_mensuel': '900.00',  # Modifié
            'charges_mensuelles': '100.00',
            'jour_echeance': 5,
            'actif': True
        }

        response = self.client.post(url, data)

        self.contrat.refresh_from_db()
        self.assertEqual(self.contrat.loyer_mensuel, Decimal("900.00"))

    def test_contrat_delete(self):
        """Test la suppression d'un contrat"""
        self.client.login(email="test@example.com", password="testpass123")
        url = reverse('contrats:contrat_delete', kwargs={'pk': self.contrat.pk})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Contrats.objects.filter(pk=self.contrat.pk).exists())

    def test_contrat_locataires_list_view(self):
        """Test la vue de liste des locataires d'un contrat"""
        self.client.login(email="test@example.com", password="testpass123")
        self.contrat.ajouter_locataire(self.locataire)

        url = reverse('contrats:contrat_locataires', kwargs={'contrat_id': self.contrat.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contrats/contrat_locataire_list.html')
        self.assertIn('locataires_actifs', response.context)
        self.assertEqual(response.context['nb_actifs'], 1)

    def test_ajouter_locataire_view_post(self):
        """Test l'ajout d'un locataire à un contrat"""
        self.client.login(email="test@example.com", password="testpass123")

        locataire2 = Locataires.objects.create(
            nom="New",
            prenom="Tenant",
            email="new@example.com",
            telephone="0623456789"
        )

        url = reverse('contrats:ajouter_locataire', kwargs={'contrat_id': self.contrat.id})
        data = {
            'locataire': locataire2.id,
            'principal': True,
            'role': 'titulaire'
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ContratLocataire.objects.filter(contrat=self.contrat, locataire=locataire2).exists()
        )

    def test_definir_principal_view(self):
        """Test la définition d'un locataire comme principal"""
        self.client.login(email="test@example.com", password="testpass123")

        self.contrat.ajouter_locataire(self.locataire, principal=False)
        relation = ContratLocataire.objects.get(contrat=self.contrat, locataire=self.locataire)

        url = reverse('contrats:definir_principal', kwargs={
            'contrat_id': self.contrat.id,
            'relation_id': relation.id
        })

        response = self.client.post(url)

        relation.refresh_from_db()
        self.assertTrue(relation.principal)

    def test_retirer_locataire_view(self):
        """Test le retrait d'un locataire"""
        self.client.login(email="test@example.com", password="testpass123")

        self.contrat.ajouter_locataire(self.locataire)
        relation = ContratLocataire.objects.get(contrat=self.contrat, locataire=self.locataire)

        url = reverse('contrats:retirer_locataire', kwargs={
            'contrat_id': self.contrat.id,
            'relation_id': relation.id
        })

        data = {'date_sortie': '2024-06-30'}
        response = self.client.post(url, data)

        relation.refresh_from_db()
        self.assertIsNotNone(relation.date_sortie)
        self.assertEqual(relation.date_sortie, date(2024, 6, 30))


class ContratsURLsTestCase(TestCase):
    """Tests pour les URLs de l'app contrats"""

    def test_contrats_list_url(self):
        """Test la résolution de l'URL de liste"""
        url = reverse('contrats:contrats_list')
        self.assertEqual(url, '/contrats/list/')

    def test_contrat_create_url(self):
        """Test la résolution de l'URL de création"""
        url = reverse('contrats:contrat_create')
        self.assertEqual(url, '/contrats/create/')

    def test_contrat_update_url(self):
        """Test la résolution de l'URL de modification"""
        url = reverse('contrats:contrat_update', kwargs={'pk': 1})
        self.assertEqual(url, '/contrats/update/1/')

    def test_contrat_delete_url(self):
        """Test la résolution de l'URL de suppression"""
        url = reverse('contrats:contrat_delete', kwargs={'pk': 1})
        self.assertEqual(url, '/contrats/delete/1/')

    def test_contrat_locataires_url(self):
        """Test la résolution de l'URL de gestion des locataires"""
        url = reverse('contrats:contrat_locataires', kwargs={'contrat_id': 1})
        self.assertEqual(url, '/contrats/1/locataires/')

    def test_ajouter_locataire_url(self):
        """Test la résolution de l'URL d'ajout de locataire"""
        url = reverse('contrats:ajouter_locataire', kwargs={'contrat_id': 1})
        self.assertEqual(url, '/contrats/1/locataires/ajouter/')


class ContratsFormsTestCase(TestCase):
    """Tests pour les formulaires de l'app contrats"""

    def setUp(self):
        """Prépare les données pour les tests"""
        self.proprietaire = Proprietaires.objects.create(
            nom="Test",
            prenom="Owner",
            email="owner@example.com",
            telephone="0123456789"
        )

        self.immeuble = Immeuble.objects.create(
            nom="Test Building",
            adresse="123 Test St",
            ville="Paris",
            code_postal="75001"
        )

        self.appartement = Appartement.objects.create(
            immeuble=self.immeuble,
            numero="101",
            proprietaire=self.proprietaire,
            etage=1
        )

        self.locataire = Locataires.objects.create(
            nom="Test",
            prenom="Tenant",
            email="tenant@example.com",
            telephone="0612345678"
        )

        self.contrat = Contrats.objects.create(
            appartement=self.appartement,
            date_debut=date(2024, 1, 1),
            loyer_mensuel=Decimal("800.00")
        )

    def test_contrat_form_valid(self):
        """Test un formulaire valide"""
        from .forms import ContratForm

        data = {
            'appartement': self.appartement.id,
            'date_debut': date(2024, 1, 1),
            'loyer_mensuel': Decimal("800.00"),
            'charges_mensuelles': Decimal("100.00"),
            'jour_echeance': 5,
            'actif': True
        }

        form = ContratForm(data=data)
        self.assertTrue(form.is_valid())

    def test_contrat_form_invalid_jour_echeance(self):
        """Test validation du jour d'échéance"""
        from .forms import ContratForm

        data = {
            'appartement': self.appartement.id,
            'date_debut': date(2024, 1, 1),
            'loyer_mensuel': Decimal("800.00"),
            'jour_echeance': 32,  # Invalide
            'actif': True
        }

        form = ContratForm(data=data)
        self.assertFalse(form.is_valid())

    def test_ajouter_locataire_form_exclut_deja_sur_contrat(self):
        """Test que le formulaire exclut les locataires déjà sur le contrat"""
        from .forms import AjouterLocataireContratForm

        # Ajouter un locataire au contrat
        self.contrat.ajouter_locataire(self.locataire)

        # Créer un autre locataire
        locataire2 = Locataires.objects.create(
            nom="Other",
            prenom="Tenant",
            email="other@example.com",
            telephone="0623456789"
        )

        form = AjouterLocataireContratForm(contrat=self.contrat)

        # Le premier locataire ne doit pas être dans les choix
        locataire_ids = [choice[0] for choice in form.fields['locataire'].choices if choice[0]]
        self.assertNotIn(self.locataire.id, locataire_ids)
        self.assertIn(locataire2.id, locataire_ids)

    def test_contrat_locataire_form_validation_dates(self):
        """Test la validation des dates (sortie > entrée)"""
        from .forms import ContratLocataireForm

        data = {
            'locataire': self.locataire.id,
            'date_entree': date(2024, 6, 1),
            'date_sortie': date(2024, 5, 1),  # Avant la date d'entrée
            'ordre': 1,
            'role': 'titulaire'
        }

        form = ContratLocataireForm(data=data, contrat=self.contrat)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)