from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(_('name'), max_length=200, unique=True)
    color = models.CharField(_('color'), max_length=7, null=True, unique=True)
    slug = models.SlugField(_('slug'), unique=True)

    class Meta:
        ordering = ['pk']
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(_('name'), max_length=200)
    measurement_unit = models.CharField(_('measurement unit'), max_length=200)

    class Meta:
        ordering = ['pk']
        verbose_name = _('Ingredient')
        verbose_name_plural = _('Ingredients')

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   verbose_name=_('ingredient'))
    amount = models.IntegerField(_('amount'), default=1)

    class Meta:
        ordering = ['pk']
        verbose_name = _('Ingredient in recipe')
        verbose_name_plural = _('Ingredients in recipe')

    def __str__(self):
        return (f'{self.ingredient.name} - {self.amount} '
                f'{self.ingredient.measurement_unit}')


class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='recipes',
                               verbose_name=_('author'))
    pub_date = models.DateTimeField(_('date published'), auto_now_add=True)
    name = models.CharField(_('name'), max_length=200)
    image = models.ImageField(_('image'), upload_to='images/')
    text = models.TextField(_('description'))
    ingredients = models.ManyToManyField(IngredientInRecipe,
                                         related_name='recipes',
                                         verbose_name=_('ingredients'))
    tags = models.ManyToManyField(Tag, related_name='recipes',
                                  verbose_name=_('tags'))
    cooking_time = models.PositiveSmallIntegerField(_('cooking time'))

    class Meta:
        ordering = ['-pub_date']
        verbose_name = _('Recipe')
        verbose_name_plural = _('Recipes')

    def __str__(self):
        return self.name


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='favorites',
                             verbose_name=_('user'))
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='favorites',
                               verbose_name=_('recipe'))

    class Meta:
        verbose_name = _('Favorite')
        verbose_name_plural = _('Favorites')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='purchases',
                             verbose_name=_('user'))
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='buyers',
                               verbose_name=_('recipe'))

    class Mete:
        verbose_name = _('Cart')
        verbose_name_plural = _('Carts')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='subscriptions',
                             verbose_name=_('user'))
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='subscribers',
                               verbose_name=_('author'))

    class Meta:
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.author.username}'
