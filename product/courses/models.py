from django.db import models
from .fields import OrderField

from users.user_model import CustomUser as User


class CourseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_available=True)


class Course(models.Model):
    """Модель продукта - курса."""

    MAX_STUDENTS_QUANTITY = 300 # Максимальное кол-во студентов на курсе

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='courses'
    )

    # Да, группы курса связаны с курсом, а в самих группах хранится
    # информация об студентах, но решил добавить сюда тоже связь со
    # студентами, чтобы постоянно не обращаться к группам, которых тем
    # более 10 ( ну или же по подпискам пользователя, которых тоже много).
    students = models.ManyToManyField(
        User,
        related_name='joined_courses',
        blank=True
    )

    title = models.CharField(
        max_length=250,
        verbose_name='Название',
    )
    # Не Decimal т.к реализуется ведь купонная система, в которых, на сколько
    # знаю, купоны могут измеряться только целыми числами.
    price = models.PositiveIntegerField(default=0)

    # Буду отображать только доступные для покупки курсы. Когда у курса
    # количество студентов == 300, курс автоматически станет недоступным
    # к покупке и не будет отображаться в общем списке.
    is_available = models.BooleanField(default=True)
    start_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время начала курса'
    )

    available = CourseManager()
    objects = models.Manager()

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ('-id',)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """Модель урока."""

    course = models.ForeignKey(Course,
                               on_delete=models.CASCADE,
                               related_name='lessons')

    title = models.CharField(
        max_length=250,
        verbose_name='Название',
    )
    link = models.URLField(
        max_length=250,
        verbose_name='Ссылка',
    )

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ('id',)

    def __str__(self):
        return self.title


class Group(models.Model):
    """Модель группы."""

    MAX_STUDENTS_QUANTITY = 30 # Максимальное количество студентов в группе

    # "Группа А", "Группа Б" ...
    title = models.CharField(max_length=150)

    # Номер будет формироваться относительно курса
    number = OrderField(blank=True, fields=['course'])

    course = models.ForeignKey(Course,
                               on_delete=models.CASCADE,
                               related_name='groups')
    students = models.ManyToManyField(User,
                                      related_name='joined_groups',
                                      blank=True)

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        # Отображаем в последовательности по number, тем самым обеспечим,
        # что в будущем можно легко будет менять последовательность уроков
        # в курсе - фронтендер должен будет сообщить лишь новую
        # последовательность для всех уроков курса.
        ordering = ('number',)
