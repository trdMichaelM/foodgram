from django.contrib.auth import get_user_model
from rest_framework import serializers

from recipes.models import (Recipe, Tag, Ingredient, IngredientInRecipe,
                            TagForRecipe, IngredientInRecipeForRecipe)

User = get_user_model()


class Base64Image(serializers.Field):
    pass
#     # При чтении данных ничего не меняем - просто возвращаем как есть
#     def to_representation(self, value):
#         return value
#     # При записи код цвета конвертируется в его название
#     def to_internal_value(self, data):
#         # Доверяй, но проверяй
#         try:
#             # Если имя цвета существует, то конвертируем код в название
#             data = webcolors.hex_to_name(data)
#         except ValueError:
#             # Иначе возвращаем ошибку
#             raise serializers.ValidationError('Для этого цвета нет имени')
#         # Возвращаем данные в новом формате
#         return data


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        return False
        # TODO:


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    # ingredient = IngredientSerializer()
    id = serializers.CharField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = IngredientInRecipeSerializer(many=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64Image()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    def create(self, validated_data):
        pass
        # TODO

    def get_is_favorited(self, obj):
        return False
        # TODO:

    def get_is_in_shopping_cart(self, obj):
        return False
        # TODO:
