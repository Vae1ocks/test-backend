from django.shortcuts import get_object_or_404
from django.db.models import Count, F
from django.db import transaction

from rest_framework.response import Response
from rest_framework import status

from users.models import Subscription
from courses.models import Course, Group


def make_payment(user, user_balance, course, price):
    with transaction.atomic():
        user_balance.bonuses = F('bonuses') - price
        user_balance.save()
        subscription = Subscription.objects.create(
            user=user,
            course=course
        )
        course.students.add(user)
    return subscription