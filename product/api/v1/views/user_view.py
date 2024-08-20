from django.contrib.auth import get_user_model
from rest_framework import permissions, viewsets

from api.v1.serializers.user_serializer import (CustomUserSerializer,
                                                UserAdminEditSerializer)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related('balance')
    serializer_class = CustomUserSerializer
    http_method_names = ["get", "head", "options", "patch"]
    # Админ может изменить информацию о пользователе, в том числе
    # и баланс, используя API.
    permission_classes = (permissions.IsAdminUser,)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve", "head", "options"]:
            return CustomUserSerializer
        return UserAdminEditSerializer

