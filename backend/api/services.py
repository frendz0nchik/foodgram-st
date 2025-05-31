from django.db.models import Sum
from datetime import date
from django.http import HttpResponse
from recipes.models import IngredientRecipe


def download_shopping_cart(request, author):
    """Скачивание списка продуктов для выбранных рецептов пользователя."""
    ingredients_summary = IngredientRecipe.objects.filter(
        recipe__shopping_cart__author=author
    ).values(
        'ingredient__name', 'ingredient__measurement_unit'
    ).annotate(
        total_amount=Sum('amount', distinct=True)
    ).order_by('total_amount')

    today = date.today().strftime("%d-%m-%Y")
    shopping_list = f'Список покупок на: {today}\n\n'

    for ingredient in ingredients_summary:
        shopping_list += (
            f'{ingredient["ingredient__name"]} - '
            f'{ingredient["total_amount"]} '
            f'{ingredient["ingredient__measurement_unit"]}\n'
        )

    shopping_list += '\n\nFoodgram (2025)'
    filename = 'shopping_list.txt'
    response = HttpResponse(shopping_list, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response