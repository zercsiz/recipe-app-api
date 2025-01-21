"""
Tests for recipe API.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)



RECIPES_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    """Create and return a recipe detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe."""

    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'http://example.com/recipe.pdf',
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """Helper function to create a new user."""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test aunauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()


    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email = 'user@example.com', password = 'testpass123')
        self.client.force_authenticate(self.user)


    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user."""
        other_user = create_user(email = 'user2@example.com', password = 'pass28976')

        create_recipe(user=self.user)
        create_recipe(user=other_user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


    def test_get_recipe_detail(self):
        """Test get recipe detail."""
        recipe = create_recipe(user=self.user)
        serializer = RecipeDetailSerializer(recipe)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        self.assertEqual(res.data, serializer.data)


    def test_create_recipe(self):
        """Test creating a recipe."""

        payload = {
            'title': 'sample recipe',
            'time_minutes': 30,
            'price': Decimal('20.50')
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)
        self.assertEqual(recipe.user, self.user)


    def test_partial_update(self):
        """Test partial update for a recipe."""

        original_link = 'https://testapi.com/recipe1.pdf'
        recipe = create_recipe(
            user = self.user,
            title = 'sample title',
            link = original_link,
        )
        payload = {
            'title': 'Update Title'
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)


    def test_full_update(self):
        """Test full update for a recipe."""
        recipe = create_recipe(
            user = self.user,
            title = 'original title',
            link = 'http://testapi.com/recipe1.pdf',
            description = 'description for a recipe'
        )

        payload = {
            'title': 'new title',
            'link': 'http://testapi.com/newrecipe.pdf',
            'description': 'new description for a recipe',
            'time_minutes': 50,
            'price': Decimal('330.0')
        }

        url = detail_url(recipe.id)

        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)
        self.assertEqual(recipe.user, self.user)


    def update_user_returns_error(self):
        """Test changing a recipe user results in an error."""
        new_user = create_user(email = 'newuser@example.com', password = 'newpass234')
        recipe = create_recipe(user = self.user)

        payload = {
            'user': new_user.id
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)


    def test_delete_recipe(self):
        """Test deleting a recipe is successful."""
        recipe = create_recipe(user = self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())


    def test_delete_other_users_recipe_error(self):
        """Test deleting other users recipe returns error."""
        other_user = create_user(email='other@example.com', password='otherpass213')
        recipe = create_recipe(user=other_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())


    def test_create_recipe__with_new_tags(self):
        """Test creating a recipe with new tags.
            Because we create tags when we create recipes.
            Not create them separately.
        """

        payload = {
            'title': 'qorme sabzi',
            'time_minutes': 120,
            'price': Decimal('25.00'),
            'tags': [
                {'name': 'dinner'},
                {'name': 'luxury'}
            ]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = Tag.objects.filter(user=self.user, name=tag['name'])
            self.assertTrue(exists)


    def test_create_recipe_with_existing_tag(self):
        """Test creating recipe with existing tag."""

        indian_tag = Tag.objects.create(user=self.user, name='indian')

        payload = {
            'title': 'some food name',
            'time_minutes': 60,
            'price': Decimal('5.60'),
            'tags': [{'name': 'indian'}, {'name': 'breakfast'}],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(indian_tag, recipe.tags.all())

        for tag in payload['tags']:
            exists = recipe.tags.filter(name=tag['name'], user=self.user).exists()

            self.assertTrue(exists)


    def test_create_tag_on_recipe_update(self):
        """Test create tag on recipe update."""

        recipe = create_recipe(user=self.user)
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')

        # you dont need to refresh_from_db for many to many fields
        # when doing recipe.tags.all() it is a new query so its updated
        self.assertIn(new_tag, recipe.tags.all())


    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe."""
        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')

        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_lunch)

        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        payload = {'tags': [{'name': 'Breakfast'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_breakfast, recipe.tags.all())
        self.assertNotIn(tag_lunch, recipe.tags.all())


    def test_clear_recipe_tags(self):
        """Test clearing a recipes tags."""

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_lunch)

        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)


    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients."""

        payload = {'title': 'some recipe',
                   'time_minutes': 89,
                   'price': Decimal('8.9'),
                   'ingredients': [{'name': 'ing1'}, {'name': 'ing2'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(name=ingredient['name'], user=self.user).exists()
            self.assertTrue(exists)


    def test_create_recipe_with_existing_ingredients(self):
        """Test creating a new recipe with existing ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name='Lemon')
        payload = {'title': 'some recipe',
                   'time_minutes': 89,
                   'price': Decimal('8.9'),
                   'ingredients': [{'name': 'Lemon'}, {'name': 'ing2'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]

        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(name=ingredient['name'], user=self.user).exists()
            self.assertTrue(exists)



    def test_create_ingredient_on_update(self):
        """Test creating an ingredient when updating a recipe."""
        recipe = create_recipe(user=self.user)

        payload = {'ingredients': [{'name': 'Limes'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_ingredient = Ingredient.objects.get(user=self.user, name='Limes')
        self.assertIn(new_ingredient, recipe.ingredients.all())


    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe."""

        ingredient1 = Ingredient.objects.create(user=self.user, name='Pepper')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='Chili')
        payload = {'ingredients': [{'name': 'Chili'}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())


    def test_clear_recipe_ingredients(self):
        """test clearing a recipes ingredients."""

        ingredient = Ingredient.objects.create(user=self.user, name='Garlic')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {'ingredients': []}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)