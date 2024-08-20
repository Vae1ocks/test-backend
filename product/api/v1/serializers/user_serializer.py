from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from rest_framework import serializers

from users.models import Subscription

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """
    Сериализатор пользователя для просмотра его данных.
    """
    bonuses = serializers.IntegerField(source='balance.bonuses',
                                       read_only=True)

    class Meta:
        model = User
        exclude = ['password']


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки."""

    user = serializers.StringRelatedField() # user.get_full_name()

    class Meta:
        model = Subscription
        fields = '__all__'


class UserAdminEditSerializer(serializers.ModelSerializer):
    """
    Сериализатор для возможности редактирования админом пользовательского
    профиля, ограниченный нечувствительной информацией - username,
    first_name и last_name. Так же возможность редактировать баланс
    пользователя.
    """

    bonuses = serializers.IntegerField(min_value=0, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'bonuses']

    def update(self, instance, validated_data):
        bonuses = validated_data.pop('bonuses', None)
        if bonuses:
            # Меняем количество бонусов на счету у пользователя,
            # если это количество передано.
            instance.balance.bonuses = bonuses
            instance.balance.save()
        return super().update(instance, validated_data)


class UserPersonalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
