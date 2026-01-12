from django.test import TestCase
from django.urls import reverse

class AccountURLsTestCase(TestCase):
    """Tests pour les URLs de l'app contrats"""

    def test_login_url(self):
        """Test la résolution de l'URL de liste"""
        url = reverse('accounts:login')
        self.assertEqual(url, '/accounts/login/')

    def test_logout_url(self):
        """Test la résolution de l'URL de liste"""
        url = reverse('accounts:logout')
        self.assertEqual(url, '/accounts/logout/')


    def test_profile_url(self):
        """Test la résolution de l'URL de modification"""
        url = reverse('accounts:profile')
        self.assertEqual(url, '/accounts/profile/')


    def test_user_create_url(self):
        """Test la résolution de l'URL de modification"""
        url = reverse('accounts:create_user')
        self.assertEqual(url, '/accounts/users/create/')