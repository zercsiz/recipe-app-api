""""
Tests for models.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from decimal import Decimal
from core import models


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """Test creating user with email is successful."""

        # it is recommended that you use @example.com for tests
        email = "user@example.com"
        password = "testpassword87"

        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users"""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test that creating a user without an email raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_superuser(self):
        """Test creating a superuser"""

        user = get_user_model().objects.create_superuser(
            'user@example.com',
            'passwsnsjsj2'
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


    def test_create_recipe(self):
        """Test creating recipe is successful."""
        user = get_user_model().objects.create_user(
            email = 'test@example.com',
            password = 'goodpass123',
            name = 'Test Name',
        )

        recipe = models.Recipe.objects.create(
            user = user,
            title = 'Sample recipe name',
            time_minutes = 5,
            price = Decimal('5.50'),
            description = 'Sample recipe description',
        )

        self.assertEqual(str(recipe), recipe.title)