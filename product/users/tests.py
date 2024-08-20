from django.test import TestCase
from django.contrib.auth import get_user_model

from .models import Balance

User = get_user_model()


def user_create(username='Test', email='test@test.com', first_name='FirstName',
             last_name='LastName', password='password123'):
    return User.objects.create_user(username=username, email=email,
                                    first_name=first_name,
                                    last_name=last_name,
                                    password=password)


class UsersModelsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = user_create()
        cls.user = user
        cls.email = user.email
        cls.username = user.username
        cls.first_name = user.first_name
        cls.last_name = user.last_name

    def test_user_create(self):
        user = User.objects.first()
        self.assertEqual(user.email, self.email)
        self.assertEqual(user.username, self.username)
        self.assertEqual(user.first_name, self.first_name)
        self.assertEqual(user.last_name, self.last_name)

        balance = Balance.objects.first()
        self.assertIsNotNone(balance)
        self.assertEqual(balance.user, user)
        self.assertEqual(balance.bonuses, 1000)
