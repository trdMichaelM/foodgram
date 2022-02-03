from django.contrib import admin

from .models import (Recipe, Tag, Ingredient, IngredientInRecipe, Favorite,
                     Cart, Subscription)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_filter = ('author', 'name', 'tags')
    fields = ('author', 'name', 'image', 'text', 'ingredients', 'tags',
              'cooking_time', 'count_favorite')
    readonly_fields = ('count_favorite',)

    def count_favorite(self, obj):
        return obj.favorites.count()


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(IngredientInRecipe, admin.ModelAdmin)
admin.site.register(Favorite, admin.ModelAdmin)
admin.site.register(Cart, admin.ModelAdmin)
admin.site.register(Subscription, admin.ModelAdmin)
