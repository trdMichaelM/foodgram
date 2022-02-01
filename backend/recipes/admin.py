from django.contrib import admin

from .models import (Recipe, Tag, Ingredient, IngredientInRecipe, Favorite,
                     Cart, Subscription)


# class UserAdmin(admin.ModelAdmin):
#     list_display = ('username', 'first_name', 'last_name', 'email')
#     search_fields = ('email', 'username')
#     list_filter = ('email', 'username')
#     empty_value_display = '-empty-'


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_filter = ('author', 'name', 'tags')
    fields = ('author', 'name', 'image', 'text', 'ingredients', 'tags',
              'cooking_time', 'count_favorite')
    readonly_fields = ('count_favorite',)

    def count_favorite(self, object):
        return object.favorites.count()


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


class IngredientInRecipeAdmin(admin.ModelAdmin):
    pass


class FavoriteAdmin(admin.ModelAdmin):
    pass


class CartAdmin(admin.ModelAdmin):
    pass


class SubscriptionAdmin(admin.ModelAdmin):
    pass


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(IngredientInRecipe, IngredientInRecipeAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
