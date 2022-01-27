from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import (ValidationError as
                                    ValidationErrorFromDjangoCore)
from django.contrib.auth.hashers import check_password
from django.db.models import BooleanField, Value, Exists, OuterRef
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import status
from rest_framework import mixins

from recipes.models import (Recipe, Tag, Ingredient, Subscription, Favorite,
                            Cart)

from .serializers import (UserSerializer, RecipeSerializer, TagSerializer,
                          IngredientSerializer, SetPasswordSerializer,
                          FavoriteSerializer, SubscriptionSerializer)
from .permissions import IsOwnerPermission

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer

    permission_classes = [permissions.IsAuthenticated]

    http_method_names = ['get', 'post']

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            queryset = User.objects.all().annotate(
                is_subscribed=Exists(Subscription.objects.filter(
                    user=user, author__pk=OuterRef('pk'))
                )
            )
            return queryset

        queryset = User.objects.all().annotate(
            is_subscribed=Value(False, output_field=BooleanField())
        )
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

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            queryset = Recipe.objects.all().annotate(
                is_favorited=Exists(Favorite.objects.filter(
                    user=user, recipe__pk=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(Cart.objects.filter(
                    user=user, recipe__pk=OuterRef('pk'))
                )
            )
            return queryset

        queryset = Recipe.objects.all().annotate(
            is_favorited=Value(False, output_field=BooleanField()),
            is_in_shopping_cart=Value(False, output_field=BooleanField())
        )
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


class CreateDestroyViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin,
                           viewsets.GenericViewSet):
    pass


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


class ListCreateDestroyViewSet(mixins.ListModelMixin,
                               mixins.CreateModelMixin,
                               mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    pass


class ListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    pass


class SubscriptionListViewSet(ListViewSet):
    serializer_class = SubscriptionSerializer

    http_method_names = ['get']

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = user.subscriptions.all().annotate(
            is_subscribed=Exists(Subscription.objects.filter(
                user=user, author__pk=OuterRef('author_id'))
            )
        )
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
