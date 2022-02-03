import uuid
import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers

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
    id = serializers.CharField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

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

    def create(self, validated_data):
        tags = self.initial_data.get("tags")
        ingredients = self.initial_data.get("ingredients")
        recipe = Recipe.objects.create(**validated_data)

        for tag_id in tags:
            tag = get_object_or_404(Tag, id=tag_id)
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
        if "tags" in self.initial_data:
            tags = self.initial_data.get("tags")
            instance.tags.clear()
            for tag_id in tags:
                tag = get_object_or_404(Tag, id=tag_id)
                instance.tags.add(tag)

        if 'ingredients' in self.initial_data:
            ingredients = self.initial_data.get("ingredients")
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


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=150)
    current_password = serializers.CharField(max_length=150)


class FavoriteSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='recipe.id', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.IntegerField(source='recipe.cooking_time',
                                            read_only=True)

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, data):
        user = self.context['request'].user
        recipe_id = self.context['request'].parser_context['kwargs']['id']
        recipe = get_object_or_404(Recipe, id=recipe_id)

        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f'Recipe already favorite with current user!'
            )
        return data

    def create(self, validated_data):
        user = validated_data.get('user')
        recipe = validated_data.get('recipe')
        return Favorite.objects.create(user=user, recipe=recipe)


class SubscriptionRecipeSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    image = serializers.ImageField(read_only=True)
    cooking_time = serializers.IntegerField(read_only=True)


class SubscriptionSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source='author.email', read_only=True)
    id = serializers.CharField(source='author.id', read_only=True)
    username = serializers.CharField(source='author.username', read_only=True)
    first_name = serializers.CharField(source='author.first_name',
                                       read_only=True)
    last_name = serializers.CharField(source='author.last_name',
                                      read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes = SubscriptionRecipeSerializer(source='author.recipes', many=True,
                                           read_only=True)
    recipes_count = serializers.IntegerField(source='author.recipes.count',
                                             read_only=True)

    class Meta:
        model = Subscription
        fields = ['email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count']

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return Subscription.objects.filter(user=user,
                                           author=obj.author).exists()

    def validate(self, data):
        user = self.context['request'].user
        author_id = self.context['request'].parser_context['kwargs']['id']
        author = get_object_or_404(User, id=author_id)

        if user == author:
            raise serializers.ValidationError(
                f'Cannot subscribe yourself!'
            )

        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                f'Already subscribe with author!'
            )
        return data

    def create(self, validated_data):
        user = validated_data.get('user')
        author = validated_data.get('author')
        subscription = Subscription.objects.create(user=user, author=author)
        return subscription


class CartSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='recipe.id', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.IntegerField(source='recipe.cooking_time',
                                            read_only=True)

    class Meta:
        model = Cart
        fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, data):
        user = self.context['request'].user
        recipe_id = self.context['request'].parser_context['kwargs']['id']
        recipe = get_object_or_404(Recipe, id=recipe_id)

        if Cart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f'Recipe already in cart!'
            )
        return data

    def create(self, validated_data):
        user = validated_data.get('user')
        recipe = validated_data.get('recipe')
        return Cart.objects.create(user=user, recipe=recipe)
