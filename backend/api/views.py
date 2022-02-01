from collections import defaultdict

from xhtml2pdf import pisa

from django.template.loader import render_to_string
from django.http import HttpResponse
from django.utils.six import BytesIO
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import (ValidationError as
                                    ValidationErrorFromDjangoCore)
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import filters
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import status
from rest_framework import mixins

from recipes.models import (Recipe, Tag, Ingredient, Subscription, Favorite,
                            Cart)

from .filters import RecipeFilter
from .pagination import FoodgramPagination, SubscriptionPagination
from .serializers import (UserSerializer, UserCreateSerializer,
                          RecipeSerializer, TagSerializer,
                          IngredientSerializer, SetPasswordSerializer,
                          FavoriteSerializer, SubscriptionSerializer,
                          CartSerializer)
from .permissions import IsOwnerPermission
from .utils import fetch_resources

User = get_user_model()


class ListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    pass


class CreateDestroyViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin,
                           viewsets.GenericViewSet):
    pass


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = FoodgramPagination
    http_method_names = ['get', 'post']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        queryset = User.objects.all()
        return queryset

    def get_permissions(self):
        if self.action in ('create', 'list'):
            return (permissions.AllowAny(),)
        return super().get_permissions()

    @action(methods=['get'], detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.data.get('new_password')
        current_password = serializer.data.get('current_password')
        user = request.user
        if not check_password(current_password, user.password):
            raise ValidationError('Current password is wrong!')
        try:
            validate_password(new_password, user)
        except ValidationErrorFromDjangoCore as err:
            raise ValidationError(err)
        if current_password == new_password:
            raise ValidationError(
                'New password and current password are the same!'
            )
        user.set_password(new_password)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = FoodgramPagination
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = RecipeFilter

    def get_queryset(self):
        queryset = Recipe.objects.all()
        return queryset

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return (permissions.AllowAny(),)
        elif self.action in ('partial_update', 'destroy'):
            return (IsOwnerPermission(),)
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class IngredientReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = (filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ('^name', 'name')
    ordering_fields = ('^name', 'name')


class FavoriteViewSet(CreateDestroyViewSet):
    serializer_class = FavoriteSerializer
    queryset = Favorite.objects.all()
    http_method_names = ['post', 'delete']
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        recipe_id = self.kwargs['id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        serializer.save(user=self.request.user, recipe=recipe)

    def destroy(self, request, *args, **kwargs):
        recipe_id = kwargs['id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        user = self.request.user
        favorite_object = get_object_or_404(Favorite, user=user, recipe=recipe)
        super().perform_destroy(favorite_object)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionListViewSet(ListViewSet):
    serializer_class = SubscriptionSerializer
    http_method_names = ['get']
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SubscriptionPagination

    def get_queryset(self):
        user = self.request.user
        queryset = user.subscriptions.all()
        return queryset


class SubscriptionCreateDestroyViewSet(CreateDestroyViewSet):
    serializer_class = SubscriptionSerializer
    http_method_names = ['post', 'delete']
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        author_id = self.kwargs['id']
        author = get_object_or_404(User, id=author_id)
        serializer.save(user=self.request.user, author=author)

    def destroy(self, request, *args, **kwargs):
        author_id = kwargs['id']
        author = get_object_or_404(User, id=author_id)
        user = self.request.user
        subscription = get_object_or_404(Subscription, user=user,
                                         author=author)
        super().perform_destroy(subscription)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartListViewSet(ListViewSet):
    http_method_names = ['get']
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = request.user
        purchases = user.purchases.all()
        cart = defaultdict(int)
        for purchase in purchases:
            ingredients_in_recipe = purchase.recipe.ingredients.all()
            for ingredient_in_recipe in ingredients_in_recipe:
                amount = ingredient_in_recipe.amount
                ingredient = ingredient_in_recipe.ingredient.name
                measurement_unit = ingredient_in_recipe.ingredient.measurement_unit  # noqa
                cart[f'{ingredient} ({measurement_unit})'] += amount

        shopping_list = [f'{key} - {value}\n' for key, value in cart.items()]

        template = 'shopping_list.html'
        context = {'pagesize': 'A4', 'shopping_list': shopping_list}
        html = render_to_string(template, context)
        src = BytesIO(html.encode('utf-8'))
        dest = BytesIO()
        pisa.pisaDocument(src, dest, encoding='UTF-8',
                          link_callback=fetch_resources)
        response = HttpResponse(dest.getvalue(),
                                content_type='application/pdf')
        response['Content-Disposition'] = ('attachment; '
                                           'filename="Shopping List.pdf"')
        return response


class CartCreateDestroyViewSet(CreateDestroyViewSet):
    serializer_class = CartSerializer
    http_method_names = ['post', 'delete']
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        recipe_id = self.kwargs['id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        serializer.save(user=self.request.user, recipe=recipe)

    def destroy(self, request, *args, **kwargs):
        recipe_id = kwargs['id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        user = self.request.user
        cart = get_object_or_404(Cart, user=user, recipe=recipe)
        super().perform_destroy(cart)
        return Response(status=status.HTTP_204_NO_CONTENT)
