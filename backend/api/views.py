from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.urls import reverse

from recipes.models import Recipe, Ingredient, Favorite, ShoppingCart, User
from api.serializers import (
    RecipeListSerializer,
    IngredientSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer,
    RecipeWriteSerializer
)
from api.services import download_shopping_cart
from api.permissions import IsOwnerOrAdminOrReadOnly
from api.filters import IngredientSearchFilter, RecipeFilter
from api.paginations import ApiPagination


class IngredientViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Вьюсет для модели ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет модели Recipe: [GET, POST, DELETE, PATCH]."""
    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    pagination_class = ApiPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от метода запроса."""
        if self.request.method in SAFE_METHODS:
            return RecipeListSerializer
        return RecipeWriteSerializer

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, *args, **kwargs):
        """Добавить или удалить рецепт из избранного."""
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        user = self.request.user

        if request.method == 'POST':
            if Favorite.objects.filter(author=user, recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже добавлен!'}, status=status.HTTP_400_BAD_REQUEST)

            serializer = FavoriteSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save(author=user, recipe=recipe)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not Favorite.objects.filter(author=user, recipe=recipe).exists():
            return Response({'errors': 'Объект не найден'}, status=status.HTTP_404_NOT_FOUND)

        Favorite.objects.get(recipe=recipe).delete()
        return Response('Рецепт успешно удалён из избранного.', status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, **kwargs):
        """Добавить или удалить рецепт из списка покупок."""
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        user = self.request.user

        if request.method == 'POST':
            if ShoppingCart.objects.filter(author=user, recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже добавлен!'}, status=status.HTTP_400_BAD_REQUEST)

            serializer = ShoppingCartSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save(author=user, recipe=recipe)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not ShoppingCart.objects.filter(author=user, recipe=recipe).exists():
            return Response({'errors': 'Объект не найден'}, status=status.HTTP_404_NOT_FOUND)

        ShoppingCart.objects.get(recipe=recipe).delete()
        return Response('Рецепт успешно удалён из списка покупок.', status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Скачать список покупок для выбранных рецептов."""
        author = User.objects.get(id=self.request.user.pk)
        if author.shopping_cart.exists():
            return download_shopping_cart(request, author)
        return Response('Список покупок пуст.', status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_recipe_link(self, request, pk=None):
        """Генерирует полную ссылку на рецепт."""
        recipe = self.get_object()
        absolute_url = request.build_absolute_uri(reverse('recipes-detail', kwargs={'pk': recipe.id}))
        return Response({'short-link': absolute_url})
