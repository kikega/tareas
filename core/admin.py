from django.contrib import admin
from .models import User, Category, Tag, Project, Task, Subtask, TimeLog

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'color')
    search_fields = ('name', 'user__email')
    list_filter = ('user',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'color')
    search_fields = ('name', 'user__email')
    list_filter = ('user',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    search_fields = ('name', 'user__email')
    list_filter = ('user',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'user', 'status', 'category', 'created_at')
    search_fields = ('title', 'project__name', 'user__email')
    list_filter = ('status', 'project', 'user', 'category')

@admin.register(Subtask)
class SubtaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'task', 'user', 'is_completed')
    search_fields = ('title', 'task__title', 'user__email')
    list_filter = ('is_completed', 'user')

@admin.register(TimeLog)
class TimeLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'task', 'subtask', 'start_time', 'end_time')
    search_fields = ('user__email', 'task__title', 'subtask__title')
    list_filter = ('user', 'start_time')
