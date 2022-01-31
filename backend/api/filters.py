from django_filters import rest_framework

from recipes.models import Recipe


class RecipeFilter(rest_framework.FilterSet):
    is_favorited = rest_framework.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = rest_framework.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )
    author = rest_framework.NumberFilter(field_name='author__id')
    tags = rest_framework.AllValuesMultipleFilter(field_name='tags__slug')

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(is_favorited=True)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(is_in_shopping_cart=True)
        return queryset

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author', 'tags']
