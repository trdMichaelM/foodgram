import uuid
import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import Recipe, Tag, Ingredient, IngredientInRecipe

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


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


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


class TagRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        serializer = TagSerializer(value)
        return serializer.data

    def to_internal_value(self, data):
        tag = get_object_or_404(Tag, id=data)
        return tag


class IngredientInRecipeCreateSerializer(serializers.Serializer):
    """Вспомогательный сериалайзер для IngredientInRecipeRelatedField."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField()


class IngredientInRecipeRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        serializer = IngredientInRecipeSerializer(value)
        return serializer.data

    def to_internal_value(self, data):
        serializer = IngredientInRecipeCreateSerializer(data)
        return serializer.data


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagRelatedField(many=True, queryset=Tag.objects.all())
    ingredients = IngredientInRecipeRelatedField(
        many=True,
        queryset=IngredientInRecipe.objects.all()
    )
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
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
        if 'tags' in self.validated_data:
            tags = validated_data.pop('tags')
            instance.tags.clear()
            for tag in tags:
                instance.tags.add(tag)

        if 'ingredients' in self.validated_data:
            ingredients = validated_data.pop('ingredients')
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

        super().update(instance, validated_data)

        return instance


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=150)
    current_password = serializers.CharField(max_length=150)
