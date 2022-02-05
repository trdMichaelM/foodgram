import uuid
import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import (Recipe, Tag, Ingredient, IngredientInRecipe,
                            Favorite, Subscription, Cart)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, img_str = data.split(';base64,')
            extension = format.split('/')[-1]
            id = uuid.uuid4()
            name = f'{id.urn[9:]}.{extension}'
            data = ContentFile(base64.b64decode(img_str), name=name)
        return super().to_internal_value(data)


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Subscription.objects.filter(user=user, author=obj).exists()
        return False


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IdAmountIngredientSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    def validate(self, data):
        if not Ingredient.objects.filter(id=data['id']).exists():
            raise ValidationError('Ingredient does not exist!')
        return data


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IdAmountIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image', 'name', 'text',
                  'cooking_time')

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)

        for tag in tags:
            recipe.tags.add(tag)

        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            amount = ingredient['amount']
            the_ingredient = get_object_or_404(Ingredient, id=ingredient_id)
            ingredient_in_recipe = IngredientInRecipe.objects.create(
                ingredient=the_ingredient,
                amount=amount
            )
            recipe.ingredients.add(ingredient_in_recipe)

        return recipe

    def update(self, instance, validated_data):
        if "tags" in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.clear()
            for tag in tags:
                instance.tags.add(tag)

        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.all().delete()
            instance.ingredients.clear()
            for ingredient in ingredients:
                ingredient_id = ingredient['id']
                amount = ingredient['amount']
                the_ingredient = get_object_or_404(Ingredient,
                                                   id=ingredient_id)
                ingredient_in_recipe = IngredientInRecipe.objects.create(
                    ingredient=the_ingredient,
                    amount=amount
                )
                instance.ingredients.add(ingredient_in_recipe)

        return super().update(instance, validated_data)


class RecipeReadOnlySerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Cart.objects.filter(user=user, recipe=obj).exists()
        return False


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=150)
    current_password = serializers.CharField(max_length=150)


class RecipeInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Subscription.objects.filter(user=user, author=obj).exists()
        return False

    def get_recipes(self, obj):
        request = self.context['request']
        recipes_limit = request.query_params.get('recipes_limit', None)

        if recipes_limit is None:
            recipes = Recipe.objects.filter(author=obj)
            return RecipeInfoSerializer(recipes, many=True).data

        length = int(recipes_limit)
        recipes = Recipe.objects.filter(author=obj)[:length]
        return RecipeInfoSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()
