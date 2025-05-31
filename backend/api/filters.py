from django_filters import rest_framework as filters
from rest_framework import filters as drf_filters
from recipes.models import Recipe, User


class IngredientSearchFilter(drf_filters.SearchFilter):
    """Фильтр для поиска ингредиентов по имени."""
    search_param = 'name'


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов с возможностью фильтрации по автору и статусу."""
    
    author = filters.ModelChoiceFilter(queryset=User .objects.all())
    is_in_shopping_cart = filters.BooleanFilter(method='filter_by_shopping_cart')
    is_favorited = filters.BooleanFilter(method='filter_by_favorites')

    class Meta:
        model = Recipe
        fields = ('author', 'is_favorited', 'is_in_shopping_cart')

    def filter_by_favorites(self, queryset, name, value):
        """Фильтрация по избранным рецептам."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorite__author=self.request.user)
        return queryset

    def filter_by_shopping_cart(self, queryset, name, value):
        """Фильтрация по рецептам в списке покупок."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_cart__author=self.request.user)
        return queryset