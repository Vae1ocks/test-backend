from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.v1.permissions import (IsStudentOfCourseOrIsAdmin,
                                IsStudentOfLessonOrIsAdmin,
                                ReadOnlyOrIsAdmin)
from api.v1.serializers.course_serializer import (CourseSerializer,
                                                  CourseDetailSerializer,
                                                  CreateCourseSerializer,
                                                  CreateGroupSerializer,
                                                  CreateLessonSerializer,
                                                  GroupSerializer,
                                                  LessonSerializer)
from api.v1.serializers.user_serializer import SubscriptionSerializer
from courses.models import Course
from users.models import Subscription

from api.v1.payment import make_payment


class LessonViewSet(viewsets.ModelViewSet):
    """Уроки."""

    # permission_classes = (IsStudentOrIsAdmin,)

    def get_permissions(self):
        """
        Просматривать могут только студенты и админы,
        редактировать - админы.
        """
        if self.request.method in permissions.SAFE_METHODS:
            return [IsStudentOfLessonOrIsAdmin()]
        return [permissions.IsAdminUser()]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return LessonSerializer
        return CreateLessonSerializer

    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        serializer.save(course=course)

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        if self.action == 'list':
            if not course.students.filter(id=self.request.user.id).exists():
                raise PermissionDenied('Курс не был приобретён.')
        return course.lessons.all()


class CourseViewSet(viewsets.ModelViewSet):
    """Курсы """

    def get_queryset(self):
        if self.action in ['list', 'retrieve']:
            return Course.objects.all().select_related(
                'author'
            ).prefetch_related('lessons').only(
                'title', 'start_date', 'price', 'author__first_name',
                'author__last_name', 'lessons__title'
            )
        return Course.objects.all()

    def get_permissions(self):
        if self.action == 'retrieve':
            return [IsStudentOfCourseOrIsAdmin()]
        if self.action in ['create', 'update',
                           'partial_update', 'delete']:
            return [permissions.IsAdminUser()]
        if self.action == 'pay':
            return [IsAuthenticated()]
        return [ReadOnlyOrIsAdmin()]

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseSerializer
        elif self.action == 'retrieve':
            # Использую свой CourseDetailSerializer, а не предустановленный
            # CourseSerializer, чтобы в retrieve был смысл.
            return CourseDetailSerializer
        return CreateCourseSerializer

    @action(
        methods=['post'],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def pay(self, request, pk):
        """
        Оплата курса за бонусы.
        """
        user = request.user

        course = get_object_or_404(Course, id=pk)

        if user in course.students.all():
            return Response(
                {'detail': 'Вы ужи приобрели этот курс'},
                status.HTTP_400_BAD_REQUEST
            )

        price = course.price

        user_balance = user.balance

        if user_balance.bonuses < price:
            return Response(
                {'detail': 'На вашем счету недостаточно средств'},
                status.HTTP_402_PAYMENT_REQUIRED
            )

        subscription = make_payment(
            user=user,
            user_balance=user_balance,
            course=course,
            price=price
        )

        if subscription is None:
            return Response(
                {'error': 'Произошла ошибка, повторите попытку позже'},
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            SubscriptionSerializer(subscription).data,
            status=status.HTTP_201_CREATED
        )


class GroupViewSet(viewsets.ModelViewSet):
    """Группы."""

    permission_classes = (permissions.IsAdminUser,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return GroupSerializer
        return CreateGroupSerializer

    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        serializer.save(course=course)

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        if self.action in ['list', 'retrieve']:
            return course.groups.all().select_related('course').prefetch_related(
                'students'
            ).only('title', 'course__title', 'students__email',
                   'students__first_name', 'students__last_name')
        return course.groups.all()