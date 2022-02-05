from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (UserViewSet, RecipeViewSet, TagReadOnlyModelViewSet,
                    IngredientReadOnlyModelViewSet)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagReadOnlyModelViewSet)
router.register(r'ingredients', IngredientReadOnlyModelViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path(r'auth/', include('djoser.urls.authtoken')),
]
