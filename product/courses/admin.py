from django.contrib import admin
from .models import Course, Lesson, Group


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    list_display = ('title', 'author', 'price', 'is_available', 'start_date')
    search_fields = ('title', 'author__email')
    list_filter = ('is_available', 'start_date')
    ordering = ('-id',)
    filter_horizontal = ('students',)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'number', 'course')
    search_fields = ('title', 'course__title')
    list_filter = ('course',)
    ordering = ('number',)
    filter_horizontal = ('students',)


admin.site.register(Lesson)
