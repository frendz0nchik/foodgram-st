from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from drf_extra_fields.fields import Base64ImageField
from recipes.models import Follow, Recipe
from users.models import User
import api.serializers


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения/создания пользователя модели User."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password', 'is_subscribed', 'avatar')
        extra_kwargs = {
            'password': {'write_only': True},
            'is_subscribed': {'read_only': True}
        }

    def get_is_subscribed(self, obj):
        """Проверка, подписан ли текущий пользователь на данного автора."""
        user = self.context.get('request').user
        return not user.is_anonymous and Follow.objects.filter(user=user, author=obj).exists()

    def create(self, validated_data):
        """Создание нового пользователя с шифрованием пароля."""
        return User.objects.create_user(**validated_data)


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Follow."""
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        """Проверка, подписан ли текущий пользователь на автора."""
        user = self.context.get('request').user
        return not user.is_anonymous and Follow.objects.filter(user=obj.user, author=obj.author).exists()

    def get_recipes(self, obj):
        """Получение списка рецептов автора с учетом лимита."""
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj.author)
        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]
        return api.serializers.RecipeMiniSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Получение количества рецептов автора."""
        return Recipe.objects.filter(author=obj.author).count()

    def validate(self, data):
        """Валидация данных перед созданием подписки."""
        author = self.context.get('author')
        user = self.context.get('request').user
        if Follow.objects.filter(author=author, user=user).exists():
            raise ValidationError('Вы уже подписаны на этого пользователя!', code=status.HTTP_400_BAD_REQUEST)
        if user == author:
            raise ValidationError('Невозможно подписаться на себя!', code=status.HTTP_400_BAD_REQUEST)
        return data


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        """Обновление аватара пользователя."""
        instance.avatar = validated_data['avatar']
        instance.save()
        return instance

