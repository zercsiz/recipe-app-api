"""
Serializers for recipe APIs.
"""

from rest_framework import serializers

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)



class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for Ingredient."""

    class Meta:
        model = Ingredient
        fields = ['name', 'id']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes."""

    # because we need to use tags as a nested serializer
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags', 'ingredients']
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, recipe):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user

        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,

                # because if we need to add fields to tag,
                # we dont have to change this in future.
                # it is supported automatically
                **tag
            )
            recipe.tags.add(tag_obj)

    def _get_or_create_ingredients(self, ingredients, recipe):
        """Handle getting or creating ingredients as needed."""
        auth_user = self.context['request'].user
        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(user=auth_user, **ingredient)
            recipe.ingredients.add(ingredient_obj)



    # because the nested tag is readonly,
    # we need to add functionality for the tag
    # to be created separately upon recipe creation
    def create(self, validated_data):
        """Create and return a recipe."""

        # because we need to pass validated data
        # to create recipe next and we cant pass
        # tag names for recipe creation so we pop it
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)

        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingredients(ingredients, recipe)

        return recipe


    def update(self, instance, validated_data):
        """Update a recipe."""

        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance



class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description', 'image']


# we should make a separate api for image because it is not
# best practice to send both text and image to a single api
class RecipeImageSerializer(serializers.ModelSerializer):
    """serializer for uploading images to recipes."""

    class Meta:
        model = Recipe
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}