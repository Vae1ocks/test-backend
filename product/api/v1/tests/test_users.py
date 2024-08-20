from rest_framework.test import APITestCase
from rest_framework import status

from django.urls import reverse
from django.contrib.auth import get_user_model

from users.models import Subscription, Balance
from api.v1.serializers.user_serializer import (CustomUserSerializer,
                                                SubscriptionSerializer,
                                                UserAdminEditSerializer)

User = get_user_model()


def user_create(username='Test', email='test@test.com', first_name='FirstName',
             last_name='LastName', password='password123', is_staff=True):
    return User.objects.create_user(username=username, email=email,
                                    first_name=first_name,
                                    last_name=last_name,
                                    password=password,
                                    is_staff=is_staff)


class UsersAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = 'password123'
        user = user_create(password=cls.password)
        cls.user = user
        cls.email = user.email
        cls.username = user.username
        cls.first_name = user.first_name
        cls.last_name = user.last_name

    def auth(self, email=None, password=None):
        if not email:
            email = self.email
        if not password:
            password = self.password

        is_authenticated = self.client.login(email=email,
                                             password=password)
        self.assertTrue(is_authenticated)

    def test_user_list(self):
        self.auth()
        url = reverse('users-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), 1)

        data = data[0]
        self.assertIn('bonuses', data)
        self.assertEqual(data['bonuses'], 1000)
        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['email'], self.user.email)

    def test_user_retrieve(self):
        self.auth()
        url = reverse('users-detail', args=(self.user.id,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn('bonuses', data)
        self.assertEqual(data['bonuses'], 1000)
        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['email'], self.user.email)

    def test_user_update(self):
        self.auth()
        user2 = user_create(username='Username', email='email@email.com')
        url = reverse('users-detail', args=(user2.id,))
        data = {
            'username': 'NewUsername',
            'first_name': 'New First Name',
            'last_name': 'New Last Name',
            'bonuses': 5000
        }

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user2.refresh_from_db()
        self.assertEqual(user2.balance.bonuses, data['bonuses'])
        self.assertEqual(user2.username, data['username'])
        self.assertEqual(user2.first_name, data['first_name'])
        self.assertEqual(user2.last_name, data['last_name'])

        balance = Balance.objects.first()
        self.assertEqual(balance.bonuses, data['bonuses'])
