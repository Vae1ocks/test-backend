from django.contrib.auth.models import AbstractUser
from django.db import models

from courses.models import Course
from .user_model import CustomUser


class Balance(models.Model):
    """Модель баланса пользователя."""
    user = models.OneToOneField(CustomUser,
                                on_delete=models.CASCADE,
                                related_name='balance')

    # Тут ведь купонная система, поэтому решил без DecimalField
    bonuses = models.PositiveIntegerField(default=1000)

    class Meta:
        verbose_name = 'Баланс'
        verbose_name_plural = 'Балансы'
        ordering = ('-id',)

    def __str__(self):
        return f'balance {self.bonuses} of {self.user.id}'


class Subscription(models.Model):
    """Модель подписки пользователя на курс."""
    user = models.ForeignKey(CustomUser,
                             on_delete=models.CASCADE,
                             related_name='subscriptions')
    course = models.ForeignKey(Course,
                               on_delete=models.CASCADE,
                               related_name='subscriptions')

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('-id',)

    def __str__(self):
        return f'subscription of {self.user.id} to {self.course.id}'

