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
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import status
from rest_framework import mixins

from recipes.models import (Recipe, Tag, Ingredient, Subscription, Favorite,
                            Cart)

from .filters import RecipeFilter, IngredientSearchFilter
from .pagination import FoodgramPagination
from .serializers import (UserSerializer, UserCreateSerializer,
                          RecipeReadOnlySerializer, TagSerializer,
                          IngredientSerializer, SetPasswordSerializer,
                          SubscriptionSerializer, RecipeInfoSerializer,
                          RecipeCreateSerializer)
from .permissions import IsOwnerPermission, ReadOnlyPermission
from .utils import fetch_resources

User = get_user_model()


class CreateListRetrieveViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    pass


class UserViewSet(CreateListRetrieveViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = FoodgramPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ('create', 'list'):
            # Неавторизованный пользователь может регистрироваться направляя
            # post запрос на эндпоинт http://localhost/api/users/
            # Также может просматривать список пользователей, get тудаже
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
        # ValidationError есть и в джанго и в дрф в конкретном случае мы
        # обрабатывает ValidationError из джанго
        # from django.core.exceptions import (ValidationError as
        #                                     ValidationErrorFromDjangoCore)
        # я тоже долго ее отлавливал потому что ловил из дрф :)
        except ValidationErrorFromDjangoCore as err:
            raise ValidationError(err)
        if current_password == new_password:
            raise ValidationError(
                'New password and current password are the same!'
            )
        user.set_password(new_password)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        user = self.request.user
        queryset = User.objects.filter(subscribers__user=user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionSerializer(page, many=True,
                                                context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(page, many=True,
                                            context={'request': request})
        return Response(serializer.data)

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, pk=None):
        user = self.request.user
        author = get_object_or_404(User, id=pk)

        if request.method == 'DELETE':
            subscription = get_object_or_404(Subscription, user=user,
                                             author=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if user == author:
            raise ValidationError(f'Cannot subscribe yourself!')

        if Subscription.objects.filter(user=user, author=author).exists():
            raise ValidationError(f'Already subscribe with author!')

        Subscription.objects.create(user=user, author=author)
        serializer = SubscriptionSerializer(author,
                                            context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [ReadOnlyPermission | IsOwnerPermission]
    pagination_class = FoodgramPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeReadOnlySerializer

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        instance_serializer = RecipeReadOnlySerializer(
            instance,
            context={'request': request}
        )
        return Response(instance_serializer.data,
                        status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        return serializer.save()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data,
                                         partial=True)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_update(serializer)
        instance_serializer = RecipeReadOnlySerializer(
            instance,
            context={'request': request}
        )
        return Response(instance_serializer.data)

    def perform_destroy(self, instance):
        instance.ingredients.all().delete()
        instance.delete()

    @action(methods=['get'], detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        purchases = user.purchases.select_related('recipe').prefetch_related(
            'recipe__ingredients').all()
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

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'DELETE':
            cart = get_object_or_404(Cart, user=user, recipe=recipe)
            cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if Cart.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError(f'Recipe already in cart!')

        Cart.objects.create(user=user, recipe=recipe)
        serializer = RecipeInfoSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'DELETE':
            favorite = get_object_or_404(Favorite, user=user, recipe=recipe)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError('Recipe already favorite with current user!')

        Favorite.objects.create(user=user, recipe=recipe)
        serializer = RecipeInfoSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TagReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class IngredientReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [IngredientSearchFilter]
    search_fields = ('^name',)
