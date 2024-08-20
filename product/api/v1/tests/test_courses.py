from rest_framework.test import APITestCase
from rest_framework import status

from django.urls import reverse
from django.contrib.auth import get_user_model

from courses.models import Course, Lesson, Group
from api.v1.serializers.course_serializer import (CourseSerializer,
                                                  CourseDetailSerializer)
from users.models import Subscription
from django.test.utils import CaptureQueriesContext
from django.db import connection
User = get_user_model()


def user_create(username='Test', email='test@test.com', first_name='FirstName',
             last_name='LastName', password='password123', is_staff=True):
    return User.objects.create_user(username=username, email=email,
                                    first_name=first_name,
                                    last_name=last_name,
                                    password=password,
                                    is_staff=is_staff)


def course_create(author, title='Test Course', price=10):
    return Course.objects.create(author=author, title=title, price=price)


def lesson_create(course, title='Test Lesson', link='https://example.com'):
    return Lesson.objects.create(course=course, title=title, link=link)


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

        course = course_create(author=user)
        lesson_create(course=course)

    def auth(self, email=None, password=None):
        if not email:
            email = self.email
        if not password:
            password = self.password

        is_authenticated = self.client.login(email=email,
                                             password=password)
        self.assertTrue(is_authenticated)

    def test_courses_list(self):
        url = reverse('courses-list')

        response = self.client.get(url)
        data = response.json()
        self.assertEqual(len(data), 1)

        data = data[0]
        course = Course.objects.first()
        self.assertEqual(data, CourseSerializer(course).data)
        self.assertEqual(data['students_count'], 0)
        self.assertEqual(data['groups_filled_percent'], 0)
        self.assertEqual(data['lessons_count'], 1)
        self.assertEqual(data['demand_course_percent'], 0)

    def test_course_detail(self):
        user2 = user_create(username='adfsf', email='fja@afj.com',
                            is_staff=False)
        self.auth(email=user2.email, password=self.password)
        course = Course.objects.first()
        course.students.add(user2)

        url = reverse('courses-detail', args=(course.id,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        request = response.wsgi_request
        context = {'request': request}
        self.assertEqual(
            data, CourseDetailSerializer(course, context=context).data
        )
        self.assertEqual(data['lessons_count'], 1)
        self.assertEqual(data['students_count'], 1)
        self.assertEqual(data['groups_filled_percent'], round(1 / 30 * 100, 2))
        self.assertEqual(data['lessons_count'], 1)

    def test_course_create(self):
        self.auth()
        url = reverse('courses-list')
        data = {
            'title': 'Test Course',
            'price': 1000
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        course = Course.objects.latest('id')
        self.assertEqual(course.title, data['title'])
        self.assertEqual(course.price, data['price'])

    def test_course_create_forbidden(self):
        user2 = user_create(username='adfsf', email='fja@afj.com',
                            is_staff=False)
        self.auth(email=user2.email, password=self.password)
        url = reverse('courses-list')
        data = {
            'title': 'Test Course',
            'price': 1000
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_course_payment_create(self):
        user2 = user_create(username='adfsf', email='fja@afj.com',
                            is_staff=False)
        self.auth(email=user2.email, password=self.password)
        course = Course.objects.first()
        url = reverse('courses-pay', args=(course.id,))

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        amount = user2.balance.bonuses
        user2.refresh_from_db()
        self.assertEqual(user2.balance.bonuses, amount-course.price)

        subscription = Subscription.objects.first()
        self.assertEqual(subscription.user, user2)
        self.assertEqual(subscription.course, course)

        course.refresh_from_db()
        self.assertIn(user2, course.students.all())

        self.assertEqual(Group.objects.count(), 10)
        group = Group.objects.get(course=course, number=1)
        self.assertIn(user2, group.students.all())

        user3 = user_create(username='sdsd', email='aaa@afj.com',
                            is_staff=False)
        self.auth(email=user3.email, password=self.password)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        group2 = Group.objects.get(course=course, number=2)
        self.assertIn(user3, group2.students.all())

    def test_course_payment_create_error(self):
        user2 = user_create(username='adfsf', email='fja@afj.com',
                            is_staff=False)
        self.auth(email=user2.email, password=self.password)
        course = Course.objects.first()
        url = reverse('courses-pay', args=(course.id,))
        course.students.add(user2)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_course_update(self):
        self.auth()
        course = Course.objects.first()
        url = reverse('courses-detail', args=(course.id,))
        data = {
            'title': 'New title For Course',
            'price': 8000
        }

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        course.refresh_from_db()
        self.assertEqual(course.title, data['title'])
        self.assertEqual(course.price, data['price'])

    def test_course_update_forbidden(self):
        user2 = user_create(username='adfsf', email='fja@afj.com',
                            is_staff=False)
        self.auth(email=user2.email, password=self.password)
        course = Course.objects.first()
        url = reverse('courses-detail', args=(course.id,))
        data = {
            'title': 'New title For Course',
            'price': 8000
        }

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lessons_list(self):
        user2 = user_create(username='adfsf', email='fja@afj.com',
                            is_staff=False)
        self.auth(email=user2.email, password=self.password)

        course = Course.objects.first()
        course.students.add(user2)

        course2 = course_create(author=self.user)
        lesson_create(course=course2)
        lesson_create(course=course2)
        lesson_create(course=course2)

        url = reverse('lessons-list', args=(course.id,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), 1)

        data = data[0]
        self.assertEqual(data['title'], course.lessons.first().title)
        self.assertEqual(data['course'], course.title)

    def test_lessons_list_forbidden(self):
        user2 = user_create(username='adfsf', email='fja@afj.com',
                            is_staff=False)
        self.auth(email=user2.email, password=self.password)

        course = Course.objects.first()
        url = reverse('lessons-list', args=(course.id,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_retrieve(self):
        user2 = user_create(username='adfsf', email='fja@afj.com',
                            is_staff=False)
        self.auth(email=user2.email, password=self.password)

        course = Course.objects.first()
        lesson = Lesson.objects.first()
        course.students.add(user2)
        url = reverse(
            'lessons-detail', args=(course.id, lesson.id)
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['title'], lesson.title)
        self.assertEqual(data['link'], lesson.link)
        self.assertEqual(data['course'], lesson.course.title)

    def test_lesson_retrieve_forbidden(self):
        user2 = user_create(username='adfsf', email='fja@afj.com',
                            is_staff=False)
        self.auth(email=user2.email, password=self.password)
        course = Course.objects.first()
        lesson = Lesson.objects.first()
        url = reverse(
            'lessons-detail', args=(course.id, lesson.id)
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_create(self):
        self.auth()
        course = Course.objects.first()

        url = reverse('lessons-list', args=(course.id,))
        data = {
            'title': 'New Test Lesson',
            'link': 'https://example123.com'
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 2)

        lesson = Lesson.objects.latest('id')
        self.assertEqual(lesson.title, data['title'])
        self.assertEqual(lesson.link, data['link'])
        self.assertEqual(lesson.course, course)

    def test_lesson_update(self):
        self.auth()

        course = Course.objects.first()
        lesson = Lesson.objects.first()

        url = reverse(
            'lessons-detail', args=(course.id, lesson.id)
        )
        data = {
            'title': 'New Title For Lesson Object',
            'link': 'https://newlink.com'
        }

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        lesson.refresh_from_db()
        self.assertEqual(lesson.title, data['title'])
        self.assertEqual(lesson.link, data['link'])

    def test_groups_list(self):
        self.auth()
        user2 = user_create(username='adfsf', email='fja@afj.com',
                            is_staff=False)

        course = Course.objects.first()
        course.students.add(user2)

        group = course.groups.get(number=1)
        group.students.add(user2)

        url = reverse('groups-list', args=(course.id,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), 10)

        data = data[0]
        self.assertEqual(data['title'], 'Группа А')
        self.assertEqual(data['course'], course.title)
        self.assertEqual(len(data['students']), 1)

        user_data = data['students'][0]
        self.assertEqual(user_data['first_name'], user2.first_name)
        self.assertEqual(user_data['last_name'], user2.last_name)
        self.assertEqual(user_data['email'], user2.email)

    def test_groups_list_forbidden(self):
        # HTTP_401_UNAUTHORIZED

        course = Course.objects.first()
        url = reverse('groups-list', args=(course.id,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # HTTP_403_FORBIDDEN

        user2 = user_create(username='adfsf', email='fja@afj.com',
                            is_staff=False)
        self.auth(email=user2.email, password=self.password)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_group_detail(self):
        self.auth()
        user2 = user_create(username='adfsf', email='fja@afj.com',
                            is_staff=False)

        course = Course.objects.first()
        course.students.add(user2)

        group = course.groups.get(number=1)
        group.students.add(user2)

        url = reverse('groups-detail', args=(course.id, group.id))

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['title'], 'Группа А')
        self.assertEqual(data['course'], course.title)
        self.assertEqual(len(data['students']), 1)

        user_data = data['students'][0]
        self.assertEqual(user_data['first_name'], user2.first_name)
        self.assertEqual(user_data['last_name'], user2.last_name)
        self.assertEqual(user_data['email'], user2.email)

    def test_group_delete(self):
        self.auth()

        course = Course.objects.first()
        group = course.groups.get(number=1)

        url = reverse('groups-detail', args=(course.id, group.id))

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(course.groups.count(), 9)

    def test_group_delete_forbidden(self):
        user2 = user_create(username='adfsf', email='fja@afj.com',
                            is_staff=False)
        self.auth(email=user2.email, password=self.password)

        course = Course.objects.first()
        group = course.groups.get(number=1)

        url = reverse('groups-detail', args=(course.id, group.id))

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_group_create(self):
        self.auth()

        course = Course.objects.first()

        url = reverse('groups-list', args=(course.id,))
        data = {
            'title': 'Group 0'
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(course.groups.count(), 11)

        group = course.groups.get(title=data['title'])
        self.assertEqual(group.title, data['title'])
        self.assertEqual(group.number, course.groups.count())
        self.assertEqual(group.course, course)

    def test_group_create_forbidden(self):
        user2 = user_create(username='adfsf', email='fja@afj.com',
                            is_staff=False)
        self.auth(email=user2.email, password=self.password)

        course = Course.objects.first()

        url = reverse('groups-list', args=(course.id,))
        data = {
            'title': 'Group 0'
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_group_update(self):
        self.auth()

        course = Course.objects.first()
        group = course.groups.get(number=1)

        url = reverse('groups-detail', args=(course.id, group.id))
        data = {
            'title': 'Group 0'
        }

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)



