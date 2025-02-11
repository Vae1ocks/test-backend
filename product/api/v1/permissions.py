from rest_framework.permissions import BasePermission, SAFE_METHODS
from users.models import Subscription


class IsStudentOfCourseOrIsAdmin(BasePermission):
    """
    Проверка, является ли пользователь студентом курса
    при обращении к уроку данного курса.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.students.filter(id=request.user.id).exists()


class IsStudentOfLessonOrIsAdmin(BasePermission):
    """
    Проверка, является ли пользователь студентом курса
    при обращении к данному курсу.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.course.students.filter(id=request.user.id).exists()


class ReadOnlyOrIsAdmin(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_staff or request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.method in SAFE_METHODS
