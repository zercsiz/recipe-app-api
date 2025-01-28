"""Tests for Tag API."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Tag,
    Recipe,
)

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')



def detail_url(tag_id):
    """Create and return a tag detail url."""
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='test@example.com', password='jasgd823'):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email, password)


class PublicTagApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authentication is required for retrieving tags."""

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)



class PrivateTagApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)


    def test_retrieve_tags(self):
        """Test retrieving a list of tags."""

        Tag.objects.create(user=self.user, name='tag1')
        Tag.objects.create(user=self.user, name='tag2')

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to authenticated user."""

        user2 = create_user(email='user2@example.com')
        Tag.objects.create(user=user2, name='tag2')

        tag = Tag.objects.create(user=self.user, name='tag1')

        res = self.client.get(TAGS_URL)

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_tag(self):
        """Test update tag is successful."""

        tag = Tag.objects.create(user=self.user, name='original name')

        payload = {
            'name': 'new tag name'
        }
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        tag.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(tag.name, payload['name'])


    def test_delete_tag(self):
        """Test delete a tag is successful."""
        tag = Tag.objects.create(user=self.user, name='tag1')
        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())


    def test_filter_tags_assigned_to_recipes(self):
        """Test listing tags by those assigned to recipes."""

        tag2 = Tag.objects.create(user=self.user, name='tag1')
        tag1 = Tag.objects.create(user=self.user, name='tag2')

        recipe = Recipe.objects.create(
            title='recipe1',
            time_minutes=5,
            price=Decimal('9.20'),
            user=self.user,
        )
        recipe.tags.add(tag1)
        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)


    def test_filtered_tags_unique(self):
        """Test filtered tags returns a unique list."""

        tag1 = Tag.objects.create(user=self.user, name='tag1')
        Tag.objects.create(user=self.user, name='tag2')
        recipe1 = Recipe.objects.create(
            title='recipe1',
            time_minutes=9,
            price=Decimal('6.40'),
            user=self.user,
        )
        recipe2 = Recipe.objects.create(
            title='recipe2',
            time_minutes=50,
            price=Decimal('2.78'),
            user=self.user,
        )

        recipe1.tags.add(tag1)
        recipe2.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)