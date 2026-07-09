from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard & Calendar
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('calendar/', views.calendar_view, name='calendar'),
    
    # Projects CRUD
    path('projects/', views.project_list_create, name='project_list_create'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('projects/<int:pk>/tasks/', views.project_tasks_modal, name='project_tasks_modal'),
    path('projects/<int:pk>/tasks/add/', views.project_quick_add_task, name='project_quick_add_task'),
    
    # Tasks CRUD
    path('tasks/', views.task_list_create, name='task_list_create'),
    path('tasks/<int:pk>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    
    # Subtasks
    path('tasks/<int:task_id>/subtasks/add/', views.subtask_add, name='subtask_add'),
    path('subtasks/<int:pk>/toggle/', views.subtask_toggle, name='subtask_toggle'),
    path('subtasks/<int:pk>/delete/', views.subtask_delete, name='subtask_delete'),
    
    # Categories & Tags CRUD
    path('categories/', views.category_list_create, name='category_list_create'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('tags/', views.tag_list_create, name='tag_list_create'),
    path('tags/<int:pk>/delete/', views.tag_delete, name='tag_delete'),
    
    # HTMX Timers
    path('timer/task/<int:task_id>/start/', views.start_task_timer, name='start_task_timer'),
    path('timer/task/<int:task_id>/stop/', views.stop_task_timer, name='stop_task_timer'),
    path('timer/task/<int:task_id>/finalize/', views.finalize_task, name='finalize_task'),
    
    path('timer/subtask/<int:subtask_id>/start/', views.start_subtask_timer, name='start_subtask_timer'),
    path('timer/subtask/<int:subtask_id>/stop/', views.stop_subtask_timer, name='stop_subtask_timer'),
    path('timer/subtask/<int:subtask_id>/finalize/', views.finalize_subtask, name='finalize_subtask'),
    
    # JSON APIs (for React Kanban & Charts)
    path('api/dashboard/charts-data/', views.charts_data_api, name='charts_data_api'),
    path('api/tasks/', views.tasks_api, name='tasks_api'),
    path('api/tasks/<int:task_id>/update-status/', views.task_update_status_api, name='task_update_status_api'),
]
