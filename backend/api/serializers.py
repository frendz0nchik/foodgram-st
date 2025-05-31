from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from recipes.models import Recipe, Ingredient, IngredientRecipe, ShoppingCart, Favorite
from users.serializers import UserSerializer


class BaseRecipeSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для рецептов."""
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image')
    cooking_time = serializers.IntegerField(source='recipe.cooking_time')
    id = serializers.PrimaryKeyRelatedField(source='recipe', read_only=True)

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(BaseRecipeSerializer):
    """Сериализатор для модели Favorite."""
    class Meta(BaseRecipeSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(BaseRecipeSerializer):
    """Сериализатор для модели ShoppingCart."""
    class Meta(BaseRecipeSerializer.Meta):
        model = ShoppingCart


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = '__all__',


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для связанной модели Recipe и Ingredient."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe - чтение данных."""
    author = UserSerializer()
    ingredients = IngredientRecipeSerializer(many=True, source='recipe_ingredients', read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'ingredients', 'is_favorited', 'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        """Проверка, находится ли рецепт в избранном."""
        user = self.context.get('request').user
        return not user.is_anonymous and Favorite.objects.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверка, находится ли рецепт в списке покупок."""
        user = self.context.get('request').user
        return not user.is_anonymous and ShoppingCart.objects.filter(recipe=obj).exists()


class AddIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для поля ingredient модели Recipe - создание ингредиентов."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe - запись / обновление / удаление данных."""
    ingredients = AddIngredientSerializer(many=True, write_only=True)
    image = Base64ImageField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Recipe
        fields = ('ingredients', 'image', 'name', 'text', 'cooking_time', 'author')

    def validate_ingredients(self, value):
        """Валидация ингредиентов."""
        if not value:
            raise ValidationError({'ingredients': 'Нужно выбрать ингредиент!'})
        
        ingredients_list = []
        for item in value:
            ingredient = get_object_or_404(Ingredient, name=item['id'])
            if ingredient in ingredients_list:
                raise ValidationError({'ingredients': 'Ингредиенты повторяются!'})
            if int(item['amount']) <= 0:
                raise ValidationError({'amount': 'Количество должно быть больше 0!'})
            ingredients_list.append(ingredient)
        return value

    def to_representation(self, instance):
        """Преобразование представления для рецепта."""
        ingredients = super().to_representation(instance)
        ingredients['ingredients'] = IngredientRecipeSerializer(instance.recipe_ingredients.all(), many=True).data
        return ingredients

    def add_tags_ingredients(self, ingredients, recipe):
        """Добавляет ингредиенты в рецепт."""
        IngredientRecipe.objects.bulk_create(
            [IngredientRecipe(recipe=recipe, ingredient=ingredient['id'], amount=ingredient['amount']) for ingredient in ingredients]
        )

    def create(self, validated_data):
        """Создание нового рецепта."""
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self.add_tags_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Обновление существующего рецепта."""
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        self.add_tags_ingredients(ingredients, instance)
        return super().update(instance, validated_data)


class RecipeMiniSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода рецептов в FollowSerializer."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')
