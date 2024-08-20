from django.test import TestCase
from django.db.models import Count
from django.contrib.auth import get_user_model

from .models import Course, Lesson, Group
from users.models import Subscription

User = get_user_model()


def user_create(username='Test', email='test@test.com', first_name='FirstName',
             last_name='LastName', password='password123'):
    return User.objects.create_user(username=username, email=email,
                                    first_name=first_name,
                                    last_name=last_name,
                                    password=password)


def course_create(author, title='Test Course', price=10):
    return Course.objects.create(author=author, title=title, price=price)


def lesson_create(course, title='Test Lesson', link='https://example.com'):
    return Lesson.objects.create(course=course, title=title, link=link)


def subscription_create(user, course):
    return Subscription.objects.create(user=user, course=course)


class CoursesModelsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = user_create()
        cls.user = user
        cls.email = user.email
        cls.username = user.username
        cls.first_name = user.first_name
        cls.last_name = user.last_name

        course = course_create(author=user)
        cls.course = course
        cls.course_title = course.title
        cls.course_price = course.price

        lesson = lesson_create(course=course)
        cls.lesson = lesson
        cls.lesson_title = lesson.title
        cls.lesson_link = lesson.link

    def test_course_create(self):
        course = Course.objects.first()
        self.assertIsNotNone(course)
        self.assertEqual(course.title, self.course_title)
        self.assertEqual(course.price, self.course_price)
        self.assertTrue(course.is_available)

        self.assertEqual(course.lessons.count(), 1)
        lesson = Lesson.objects.first()
        self.assertEqual(lesson.title, self.lesson_title)
        self.assertEqual(lesson.link, self.lesson_link)

        groups = course.groups.all()
        self.assertEqual(groups.count(), 10)
        self.assertEqual(groups.count(), Group.objects.count())

        names = ('А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ж', 'З', 'И', 'К')
        for num in range(groups.count()):
            group = groups[num]
            self.assertEqual(group.title, f'Группа {names[num]}')
            self.assertEqual(group.number, num + 1)

    def test_course_not_available_m2m_changed(self):
        Course.MAX_STUDENTS_QUANTITY = 1
        course = Course.objects.first()
        self.assertTrue(course.is_available)

        user2 = user_create(username='user2', email='testuser2@test.com')

        course.students.add(user2)
        self.assertEqual(course.students.count(), 1)
        self.assertFalse(course.is_available)

        course.students.remove(user2)
        self.assertEqual(course.students.count(), 0)
        self.assertTrue(course.is_available)

        course.students.add(user2)
        self.assertFalse(course.is_available)

        course.students.clear()
        self.assertEqual(course.students.count(), 0)
        self.assertTrue(course.is_available)

        Course.MAX_STUDENTS_QUANTITY = 300

    def test_subscription(self):
        user2 = user_create(username='user2', email='testuser2@test.com')
        subscription = subscription_create(user=user2,
                                           course=self.course)

        self.assertEqual(self.course.subscriptions.count(), 1)
        group = self.course.groups.annotate(
            summary_students=Count('students')
        ).order_by('-summary_students').first()

        self.assertEqual(group.number, 1)
        self.assertEqual(group.students.count(), 1)
        self.assertEqual(group.students.first(), user2)

        user3 = user_create(username='user3', email='testuser3@test.com',
                            first_name='User3')
        subscription3 = subscription_create(user=user3,
                                           course=self.course)

        user4 = user_create(username='user4', email='testuser4@test.com',
                            first_name='User4')
        subscription4 = subscription_create(user=user4,
                                           course=self.course)

        user5 = user_create(username='user5', email='testuser5@test.com',
                            first_name='User5')
        subscription5 = subscription_create(user=user5,
                                           course=self.course)

        groups = self.course.groups.annotate(
            summary_students=Count('students')
        ).order_by('-summary_students')[:User.objects.count() - 1]
        # [:User.objects.count() - 1] - отнимаем из этого числа создателя курса

        for num in range(groups.count()):
            group = groups[num]
            self.assertEqual(group.number, num + 1)
            self.assertEqual(group.students.count(), 1)