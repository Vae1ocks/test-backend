from django.contrib.auth import get_user_model
from django.db.models import Avg, Count
from django.urls import reverse

from rest_framework import serializers

from courses.models import Course, Group, Lesson
from users.models import Subscription
from .user_serializer import UserPersonalInfoSerializer

from drf_spectacular.utils import extend_schema_field

User = get_user_model()


class LessonSerializer(serializers.ModelSerializer):
    """Список уроков."""

    course = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Lesson
        fields = (
            'title',
            'link',
            'course'
        )


class LessonInCourseSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['title', 'url']

    @extend_schema_field(serializers.URLField())
    def get_url(self, obj):
        request = self.context['request']
        return request.build_absolute_uri(
            reverse('lessons-detail',
                    kwargs={
                        'course_id': obj.course_id,
                        'pk': obj.id
                    })
        )


class CreateLessonSerializer(serializers.ModelSerializer):
    """Создание уроков."""

    class Meta:
        model = Lesson
        fields = (
            'title',
            'link'
        )


class StudentSerializer(serializers.ModelSerializer):
    """Студенты курса."""

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
        )


class GroupSerializer(serializers.ModelSerializer):
    """Список групп."""

    course = serializers.StringRelatedField(read_only=True) # course.title
    students = UserPersonalInfoSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ['title', 'course', 'students']


class CreateGroupSerializer(serializers.ModelSerializer):
    """Создание групп."""

    class Meta:
        model = Group
        fields = (
            'title',
            'number'
        )


class MiniLessonSerializer(serializers.ModelSerializer):
    """Список названий уроков для списка курсов."""

    class Meta:
        model = Lesson
        fields = (
            'title',
        )


class CourseSerializer(serializers.ModelSerializer):
    """Список курсов."""

    author = serializers.StringRelatedField(read_only=True)

    lessons = MiniLessonSerializer(many=True, read_only=True)
    lessons_count = serializers.SerializerMethodField(read_only=True)
    students_count = serializers.SerializerMethodField(read_only=True)
    groups_filled_percent = serializers.SerializerMethodField(read_only=True)
    demand_course_percent = serializers.SerializerMethodField(read_only=True)

    @extend_schema_field(serializers.IntegerField())
    def get_lessons_count(self, obj):
        """Количество уроков в курсе."""
        return obj.lessons.count()

    @extend_schema_field(serializers.IntegerField())
    def get_students_count(self, obj):
        """Общее количество студентов на курсе."""
        return obj.students.count()

    @extend_schema_field(serializers.IntegerField())
    def get_groups_filled_percent(self, obj):
        """Процент заполнения групп, если в группе максимум 30 чел."""

        # Если делать это через группы, то выглядеть будет так:
        # groups = obj.groups.annotate(
        #     students_percent=Count('students') / Group.MAX_STUDENTS_QUANTITY * 100
        # )
        # average_percent = groups.aggregate(
        #     percent_avg=Avg('students_percent')
        # )['percent_avg']
        # return average_percent

        # Но т.к в самом курсе у меня есть поле students, то сделать
        # это легко через сам курс:

        all_students = obj.students.count()
        percent = all_students / Group.MAX_STUDENTS_QUANTITY * 100
        return round(percent, 2) # round по желанию

    @extend_schema_field(serializers.IntegerField())
    def get_demand_course_percent(self, obj):
        """
        Подсчёт процента приобретаемости конкретного курса.
        Учитываются только клиенты - пользователи с is_staff=False.
        """
        all_client_count = User.objects.filter(is_staff=False).count()
        all_students = obj.students.count()
        if all_client_count: # != 0
            percent = (all_students / all_client_count) * 100
            percent = round(percent, 2) # по желанию
        else:
            percent = 0
        return percent

    class Meta:
        model = Course
        fields = (
            'id',
            'author',
            'title',
            'start_date',
            'price',
            'lessons_count',
            'lessons',
            'demand_course_percent',
            'students_count',
            'groups_filled_percent',
        )


class CourseDetailSerializer(serializers.ModelSerializer):
    """
    Для отображения детальной информации о курсе и более подробной
    информации о lessons, чем в CourseSerializer, которая будет
    содержать url для перехода к детальной информации Lesson
    """
    author = serializers.StringRelatedField(read_only=True)
    lessons = LessonInCourseSerializer(many=True, read_only=True)
    lessons_count = serializers.SerializerMethodField(read_only=True)
    students_count = serializers.SerializerMethodField(read_only=True)
    groups_filled_percent = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Course
        exclude = ['students', 'is_available']

    @extend_schema_field(serializers.IntegerField())
    def get_lessons_count(self, obj):
        """Количество уроков в курсе."""
        return obj.lessons.count()

    @extend_schema_field(serializers.IntegerField())
    def get_students_count(self, obj):
        """Общее количество студентов на курсе."""
        return obj.students.count()

    @extend_schema_field(serializers.IntegerField())
    def get_groups_filled_percent(self, obj):
        """Процент заполнения групп, если в группе максимум 30 чел."""
        all_students = obj.students.count()
        percent = all_students / Group.MAX_STUDENTS_QUANTITY * 100
        return round(percent, 2) # round по желанию


class CreateCourseSerializer(serializers.ModelSerializer):
    """Создание курсов."""

    class Meta:
        model = Course
        fields = ['title', 'price']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['author'] = user
        return super().create(validated_data)