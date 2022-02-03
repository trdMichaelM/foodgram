from django.urls import include, path

from .views import (UserViewSet, RecipeViewSet, TagReadOnlyModelViewSet,
                    IngredientReadOnlyModelViewSet, FavoriteViewSet,
                    SubscriptionCreateDestroyViewSet, SubscriptionListViewSet,
                    CartCreateDestroyViewSet)
from .routers import FoodgramRouter

router = FoodgramRouter()
router.register(r'users/subscriptions', SubscriptionListViewSet,
                basename='subscriptions-list')
router.register(r'users/(?P<id>\d+)/subscribe',
                SubscriptionCreateDestroyViewSet,
                basename='subscriptions-detail')
router.register(r'recipes/(?P<id>\d+)/favorite', FavoriteViewSet)
router.register(r'recipes/(?P<id>\d+)/shopping_cart', CartCreateDestroyViewSet,
                basename='cart-detail')
router.register(r'users', UserViewSet)
router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagReadOnlyModelViewSet)
router.register(r'ingredients', IngredientReadOnlyModelViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path(r'auth/', include('djoser.urls.authtoken')),
]
