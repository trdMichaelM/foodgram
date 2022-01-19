from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='images/')
    text = models.TextField()
    # ingredients
    # tags - one to many
    cooking_time = models.PositiveIntegerField(default=1)

    # is_favorited
    # is_in_shopping_cart

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=200, unique=True)
    color = models.CharField(max_length=7, null=True, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)


class IngredientInRecipe(models.Model):
    pass


class Favorite(models.Model):
    pass
    # user
    # id recipe


class Cart(models.Model):
    pass
    # user
    # id recipe


class Subscription(models.Model):
    pass
    # id user
    # id owner
