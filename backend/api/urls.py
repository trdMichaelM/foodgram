from rest_framework.routers import DefaultRouter
from django.urls import include, path

from .views import (UserViewSet, RecipeViewSet, TagReadOnlyModelViewSet,
                    IngredientReadOnlyModelViewSet)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagReadOnlyModelViewSet)
router.register(r'ingredients', IngredientReadOnlyModelViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path(r'auth/', include('djoser.urls.authtoken')),
]
