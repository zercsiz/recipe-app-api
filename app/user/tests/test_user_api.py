"""
Tests for user API.
"""

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')

def create_user(**params):
    """Creates and returns a new user."""
    return get_user_model().objects.create_user(**params)

class PunlicUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Tests that the user creation is successful."""
        payload = {
            'email':'user@example.com',
            'password':'testpass244',
            'name':'testname',
        }

        res = self.client.post(CREATE_USER_URL, payload)

        # test that the status code is correct for created
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])

        # test the newly created user's password
        self.assertTrue(user.check_password(payload['password']))

        # test that the password hash is not included in the reponse
        # for security reasons
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists"""
        payload = {
            'email': 'user@exaplme.com',
            'password': 'testpass123',
            'name': 'testname,'
        }

        # creating the user
        create_user(**payload)

        # trying to create the user with the same email again
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test error returned if password is less than 5 characters."""
        payload = {
            'email': 'user@exaplme.com',
            'password': 'te12',
            'name': 'testname,'
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(email=payload['email']).exists()
        self.assertFalse(user_exists)


