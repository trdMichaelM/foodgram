from django.urls import include, path

from .views import (UserViewSet, RecipeViewSet, TagReadOnlyModelViewSet,
                    IngredientReadOnlyModelViewSet, FavoriteViewSet)
from .routers import FoodgramRouter

router = FoodgramRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagReadOnlyModelViewSet)
router.register(r'ingredients', IngredientReadOnlyModelViewSet)
router.register(r'recipes/(?P<id>\d+)/favorite', FavoriteViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path(r'auth/', include('djoser.urls.authtoken')),
]
