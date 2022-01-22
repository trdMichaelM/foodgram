from django.contrib import admin

from .models import Recipe, Tag, Ingredient, IngredientInRecipe

admin.site.register(Recipe)
admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(IngredientInRecipe)

