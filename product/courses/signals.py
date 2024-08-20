from django.db.models import Count
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils import timezone

from users.models import Subscription
from .models import Course, Group


@receiver(post_save, sender=Subscription)
def post_save_subscription(sender, instance: Subscription, created, **kwargs):
    """
    Распределение нового студента в группу курса.
    """

    if created:
        course = instance.course
        user = instance.user
        group = course.groups.annotate(
            summary_students=Count('students')
        ).order_by('summary_students').first()
        group.students.add(user)


@receiver(post_save, sender=Course)
def create_groups_for_course(sender, instance: Course, created, **kwargs):
    """
    Создание 10 групп для курса при создании самого курса с шаблонными
    именами групп, отражающими порядок.
    """

    if created:
        names = ('А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ж', 'З', 'И', 'К')
        for name in names:
            Group.objects.create(course=instance, title=f'Группа {name}')


@receiver(m2m_changed, sender=Course.students.through)
def check_course_availability(sender, instance, action, **kwargs):
    """
    Используется для проверки, не равно ли количество студентов,
    зачисленных на курс, максимально допустимому количеству.
    Если равно, то курс становится недоступным для приобретения с
    помощью is_available = False.
    """

    if action == 'post_add':
        if instance.students.count() == Course.MAX_STUDENTS_QUANTITY:
            instance.is_available = False
            instance.save()

    elif action == 'post_remove':
        if instance.students.count() < Course.MAX_STUDENTS_QUANTITY:
            instance.is_available = True
            instance.save()

    elif action == 'post_clear':
        instance.is_available = True
        instance.save()