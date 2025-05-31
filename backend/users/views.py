from rest_framework import viewsets, status
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.decorators import action
from djoser.serializers import SetPasswordSerializer
from rest_framework.permissions import IsAuthenticated
from api.paginations import ApiPagination
from django.shortcuts import get_object_or_404

from recipes.models import Follow
from users.models import User
from users.serializers import (
    FollowSerializer,
    UserSerializer,
    UserAvatarSerializer
)
from api.permissions import IsCurrentUserOrAdminOrReadOnly


class UserViewSet(viewsets.ModelViewSet):
    """Viewset для пользователя и подписок."""
    queryset = User.objects.all()
    permission_classes = (IsCurrentUserOrAdminOrReadOnly,)
    pagination_class = ApiPagination
    serializer_class = UserSerializer

    def perform_update(self, serializer):
        """Сохранение обновленного пользователя с учетом аватара."""
        if 'avatar' in self.request.FILES:
            serializer.save(avatar=self.request.FILES['avatar'])
        else:
            serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Получение профиля текущего пользователя."""
        user = self.request.user
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def set_password(self, request, *args, **kwargs):
        """
        Изменение пароля с помощью сериализатора
        из пакета djoser SetPasswordSerializer.
        """
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid(raise_exception=True):
            self.request.user.set_password(serializer.data["new_password"])
            self.request.user.save()
            return Response('Пароль успешно изменен', status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, *args, **kwargs):
        """Создание и удаление подписки на автора."""
        author = get_object_or_404(User, id=self.kwargs.get('pk'))
        user = self.request.user

        if request.method == 'POST':
            serializer = FollowSerializer(
                data=request.data,
                context={'request': request, 'author': author}
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save(author=author, user=user)
                return Response({'Подписка успешно создана': serializer.data}, status=status.HTTP_201_CREATED)

        if Follow.objects.filter(author=author, user=user).exists():
            Follow.objects.get(author=author, user=user).delete()
            return Response('Успешная отписка', status=status.HTTP_204_NO_CONTENT)

        return Response({'errors': 'Объект не найден'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Отображение всех подписок текущего пользователя."""
        follows = Follow.objects.filter(user=self.request.user)
        pages = self.paginate_queryset(follows)
        serializer = FollowSerializer(pages, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
        parser_classes=[JSONParser]
    )
    def avatar(self, request):
        """Обновление аватара пользователя через base64."""
        user = request.user

        if request.method == 'DELETE':
            user.avatar.delete()  # Удаляет файл и записывает NULL в БД
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = UserAvatarSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
