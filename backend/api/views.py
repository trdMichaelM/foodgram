from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import (ValidationError as
                                    ValidationErrorFromDjangoCore)
from django.contrib.auth.hashers import check_password
from django.db.models import BooleanField, Value, Exists, OuterRef
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import status

from recipes.models import (Recipe, Tag, Ingredient, Subscription, Favorite,
                            Cart)

from .serializers import (UserSerializer, RecipeSerializer, TagSerializer,
                          IngredientSerializer, SetPasswordSerializer)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    # queryset = User.objects.all().annotate(is_subscribed=Value(True, output_field=BooleanField()))
    # is_subscribed = Subscription.objects.filter()
    # queryset = User.objects.all().annotate(is_subscribed=Exists())

    serializer_class = UserSerializer

    permission_classes = [permissions.IsAuthenticated]

    http_method_names = ['get', 'post']

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

    def get_queryset(self):
        user = self.request.user
        queryset = Recipe.objects.all().annotate(
            is_favorited=Exists(Favorite.objects.filter(user=user, recipe__pk=OuterRef('pk'))),
            # is_in_shopping_cart=(Cart.objects.filter(???))
        )
        # queryset = Recipe.objects.all()
        return queryset


    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return (permissions.AllowAny(),)
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
