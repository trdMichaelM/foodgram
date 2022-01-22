from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as ValidationError_dj
from django.contrib.auth.hashers import check_password
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import status

from recipes.models import Recipe, Tag, Ingredient

from .serializers import (UserSerializer, RecipeSerializer, TagSerializer,
                          IngredientSerializer, SetPasswordSerializer)

User = get_user_model()


def login():
    """Получить токен авторизации."""
    pass


def logout():
    """Удаление токена."""
    pass


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
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
        except ValidationError_dj as err:
            raise ValidationError(err)
        user.set_password(new_password)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    http_method_names = ['get', 'post', 'patch', 'delete']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
