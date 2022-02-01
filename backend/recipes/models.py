from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(_('name'), max_length=200, unique=True)
    color = models.CharField(_('color'), max_length=7, null=True, unique=True)
    slug = models.SlugField(_('slug'), unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['pk']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'


class Ingredient(models.Model):
    name = models.CharField(_('name'), max_length=200)
    measurement_unit = models.CharField(_('measurement unit'), max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['pk']
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'


class IngredientInRecipe(models.Model):
    ingredient = models.ForeignKey(_('ingredient'), Ingredient,
                                   on_delete=models.CASCADE)
    amount = models.IntegerField(_('amount'), default=1)

    def __str__(self):
        return (f'{self.ingredient.name} - {self.amount} '
                f'{self.ingredient.measurement_unit}')

    class Meta:
        ordering = ['pk']
        verbose_name = 'Ingredient in recipe'
        verbose_name_plural = 'Ingredients in recipe'


class Recipe(models.Model):
    author = models.ForeignKey(_('author'), User, on_delete=models.CASCADE,
                               related_name='recipes')
    pub_date = models.DateTimeField(_('date published'), auto_now_add=True)
    name = models.CharField(_('name'), max_length=200)
    image = models.ImageField(_('image'), upload_to='images/')
    text = models.TextField(_('description'))
    ingredients = models.ManyToManyField(_('ingredients'), IngredientInRecipe,
                                         related_name='recipes')
    tags = models.ManyToManyField(_('tags'), Tag, related_name='recipes')
    cooking_time = models.PositiveSmallIntegerField(_('cooking time'))

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'


class Favorite(models.Model):
    user = models.ForeignKey(_('user'), User, on_delete=models.CASCADE,
                             related_name='favorites')
    recipe = models.ForeignKey(_('recipe'), Recipe, on_delete=models.CASCADE,
                               related_name='favorites')

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'

    class Meta:
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe'
            )
        ]


class Cart(models.Model):
    user = models.ForeignKey(_('user'), User, on_delete=models.CASCADE,
                             related_name='purchases')
    recipe = models.ForeignKey(_('recipe'), Recipe, on_delete=models.CASCADE,
                               related_name='buyers')

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'

    class Mete:
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe'
            )
        ]


class Subscription(models.Model):
    user = models.ForeignKey(_('user'), User, on_delete=models.CASCADE,
                             related_name='subscriptions')
    author = models.ForeignKey(_('author'), User, on_delete=models.CASCADE,
                               related_name='subscribers')

    def __str__(self):
        return f'{self.user.username} - {self.author.username}'

    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            )
        ]
