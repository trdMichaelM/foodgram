from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import status
from sqlalchemy.sql.functions import user

from recipes.models import Recipe, Tag, Ingredient

from .serializers import (UserSerializer, RecipeSerializer, TagSerializer,
                          IngredientSerializer)

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

    http_method_names = ['get', 'post']

    # @action(methods=['GET'], detail=False,
    #         permission_classes=[IsAuthenticated])
    # def me(self, request):
    #     user = request.user
    #     serializer = self.get_serializer(user)
    #     return Response(serializer.data, status=status.HTTP_200_OK)

    # @action(methods=['POST'])
    # def set_password(self, request):
    #     pass


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
