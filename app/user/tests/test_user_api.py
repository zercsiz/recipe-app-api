"""
Tests for user API.
"""

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


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


    def test_create_token_for_user(self):
        """Test generates token for valid credentials"""
        user_details = {
            'name': 'test Name',
            'email': 'user@example.com',
            'password': 'goodpass',

        }
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


    def test_create_token_bad_credentials(self):
        """Test returnes error if credentials invalid"""
        create_user(email='tset@example.com', password='goodpass')

        payload = {
            'email': 'test@example.com',
            'password': 'basspass'

        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    def test_create_token_blank_password(self):
        """Test returns error if password is blank"""
        create_user(email='test@example.com', password='goodpass')

        payload = {
            'email': 'test@example.com',
            'password': '',
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    def test_retrieve_user_unauthorized(self):
        """Test authentication is reguired for users."""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='goodpass123',
            name='test Name',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)


    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(ME_URL)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email,

        })

        self.assertEqual(res.status_code, status.HTTP_200_OK)


    def test_post_me_not_allowed(self):
        """Test post request not allowed for the me endpoint."""
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


    def test_update_user_profile(self):
        """Test update user profile for authenticated user."""
        payload = {'name': 'new Name', 'password': 'newpass123'}

        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()

        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)