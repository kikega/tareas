import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum, Count, Q

from .models import User, Project, Task, Subtask, Category, Tag, TimeLog

# --- AUTHENTICATION ---
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Verify if user exists, if not and it's a single-user system, create the first user
        if not User.objects.exists():
            user = User.objects.create_superuser(email=email, password=password)
            user.first_name = "Administrador"
            user.save()
            messages.success(request, "Primer usuario creado e iniciado sesión.")
            login(request, user)
            return redirect('dashboard')
            
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Credenciales incorrectas")
            
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# --- DASHBOARD & CALENDAR ---
@login_required
def dashboard_view(request):
    # Total counters (optimized to single Task query)
    counts = Task.objects.filter(user=request.user).aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='COMPLETED')),
        pending=Count('id', filter=Q(status='PENDING')),
        in_progress=Count('id', filter=Q(status='IN_PROGRESS'))
    )
    total_tasks = counts['total']
    completed_tasks = counts['completed']
    pending_tasks = counts['pending']
    in_progress_tasks = counts['in_progress']
    
    total_projects = Project.objects.filter(user=request.user).count()
    
    # Recent tasks: prefetch/select to avoid N+1 queries
    recent_tasks = Task.objects.filter(user=request.user).select_related('project', 'category').prefetch_related('subtasks', 'time_logs').order_by('-updated_at')[:5]
    projects = Project.objects.filter(user=request.user)
    categories = Category.objects.filter(user=request.user)
    tags = Tag.objects.filter(user=request.user)
    
    # Check if there is an active running timer (select related for task and subtask)
    active_timelogs = TimeLog.objects.filter(user=request.user, end_time__isnull=True).select_related('task', 'subtask')
    active_task = None
    active_subtask = None
    if active_timelogs.exists():
        active_log = active_timelogs.first()
        active_task = active_log.task
        active_subtask = active_log.subtask

    # Fetch recent activity logs (select related to avoid N+1 on rendering task/subtask names)
    recent_logs = TimeLog.objects.filter(user=request.user).select_related('task', 'subtask').order_by('-start_time')[:5]

    context = {
        'total_projects': total_projects,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'recent_tasks': recent_tasks,
        'projects': projects,
        'categories': categories,
        'tags': tags,
        'active_task': active_task,
        'active_subtask': active_subtask,
        'recent_logs': recent_logs,
    }
    return render(request, 'dashboard.html', context)

@login_required
def calendar_view(request):
    # Build a simple calendar context of the current month
    now = timezone.now()
    year = int(request.GET.get('year', now.year))
    month = int(request.GET.get('month', now.month))
    
    import calendar
    cal = calendar.HTMLCalendar(calendar.MONDAY)
    month_name = calendar.month_name[month]
    
    _, num_days = calendar.monthrange(year, month)
    
    # 1 single query for the whole month instead of 30!
    start_date = timezone.datetime(year, month, 1).date()
    end_date = timezone.datetime(year, month, num_days).date()
    
    tasks_in_month = list(Task.objects.filter(
        user=request.user,
        created_at__date__range=(start_date, end_date)
    ))
    
    # Group tasks by day in Python memory
    from collections import defaultdict
    tasks_by_day = defaultdict(list)
    for task in tasks_in_month:
        local_date = timezone.localdate(task.created_at)
        if local_date.year == year and local_date.month == month:
            tasks_by_day[local_date.day].append(task)
            
    days = []
    # Get day of week for the first day (0=Monday, 6=Sunday)
    first_day_of_week = calendar.weekday(year, month, 1)
    
    # Add empty days before 1st of month
    for _ in range(first_day_of_week):
        days.append({'day': 0, 'tasks': []})
        
    for day in range(1, num_days + 1):
        days.append({
            'day': day,
            'tasks': tasks_by_day[day]
        })
        
    # Calculate next and prev month
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    context = {
        'days': days,
        'year': year,
        'month': month,
        'month_name': month_name,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
    }
    return render(request, 'calendar.html', context)

# --- PROJECTS CRUD ---
@login_required
def project_list_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        if name:
            Project.objects.create(user=request.user, name=name, description=description)
            messages.success(request, "Proyecto creado con éxito.")
        return redirect('project_list_create')
        
    projects = Project.objects.filter(user=request.user).prefetch_related('tasks__time_logs').order_by('-created_at')
    return render(request, 'projects/project_list.html', {'projects': projects})

@login_required
@require_POST
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    project.delete()
    messages.success(request, "Proyecto eliminado.")
    return redirect('project_list_create')

# --- TASKS CRUD ---
@login_required
def task_list_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        project_id = request.POST.get('project')
        category_id = request.POST.get('category')
        tag_ids = request.POST.getlist('tags')
        description = request.POST.get('description', '')
        attachment = request.FILES.get('attachment')
        
        project = get_object_or_404(Project, id=project_id, user=request.user)
        category = None
        if category_id:
            category = get_object_or_404(Category, id=category_id, user=request.user)
            
        task = Task.objects.create(
            user=request.user,
            project=project,
            category=category,
            title=title,
            description=description,
            attachment=attachment
        )
        
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids, user=request.user)
            task.tags.set(tags)
            
        messages.success(request, "Tarea creada con éxito.")
        return redirect('task_list_create')
        
    tasks = Task.objects.filter(user=request.user).select_related('project', 'category').prefetch_related('tags', 'time_logs').order_by('-created_at')
    projects = Project.objects.filter(user=request.user)
    categories = Category.objects.filter(user=request.user)
    tags = Tag.objects.filter(user=request.user)
    
    # Handle HTMX request for task list filtering
    project_filter = request.GET.get('project')
    status_filter = request.GET.get('status')
    
    if project_filter:
        tasks = tasks.filter(project_id=project_filter)
    if status_filter:
        tasks = tasks.filter(status=status_filter)
        
    if request.headers.get('HX-Request'):
        return render(request, 'tasks/partials/task_table.html', {'tasks': tasks})
        
    context = {
        'tasks': tasks,
        'projects': projects,
        'categories': categories,
        'tags': tags,
    }
    return render(request, 'tasks/task_list.html', context)

@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task.objects.select_related('project', 'category').prefetch_related('tags'), pk=pk, user=request.user)
    if request.method == 'POST':
        task.title = request.POST.get('title')
        project_id = request.POST.get('project')
        category_id = request.POST.get('category')
        tag_ids = request.POST.getlist('tags')
        task.description = request.POST.get('description', '')
        
        if request.FILES.get('attachment'):
            task.attachment = request.FILES.get('attachment')
            
        task.project = get_object_or_404(Project, id=project_id, user=request.user)
        if category_id:
            task.category = get_object_or_404(Category, id=category_id, user=request.user)
        else:
            task.category = None
            
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids, user=request.user)
            task.tags.set(tags)
        else:
            task.tags.clear()
            
        task.save()
        messages.success(request, "Tarea actualizada.")
        return redirect('task_list_create')
        
    projects = Project.objects.filter(user=request.user)
    categories = Category.objects.filter(user=request.user)
    tags = Tag.objects.filter(user=request.user)
    subtasks = task.subtasks.prefetch_related('time_logs').all()
    
    context = {
        'task': task,
        'projects': projects,
        'categories': categories,
        'tags': tags,
        'subtasks': subtasks,
    }
    return render(request, 'tasks/task_edit.html', context)

@login_required
@require_POST
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.delete()
    messages.success(request, "Tarea eliminada.")
    return redirect('task_list_create')

# --- SUBTASKS ---
@login_required
@require_POST
def subtask_add(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    title = request.POST.get('title')
    if title:
        subtask = Subtask.objects.create(user=request.user, task=task, title=title)
        if request.headers.get('HX-Request'):
            return render(request, 'tasks/partials/subtask_item.html', {'subtask': subtask})
    return redirect('task_edit', pk=task.id)

@login_required
@require_POST
def subtask_toggle(request, pk):
    subtask = get_object_or_404(Subtask, pk=pk, user=request.user)
    subtask.is_completed = not subtask.is_completed
    subtask.save()
    if request.headers.get('HX-Request'):
        response = render(request, 'tasks/partials/subtask_item.html', {'subtask': subtask})
        response['HX-Trigger'] = 'time-log-updated'
        return response
    return redirect('task_edit', pk=subtask.task.id)

@login_required
@require_POST
def subtask_delete(request, pk):
    subtask = get_object_or_404(Subtask, pk=pk, user=request.user)
    task_id = subtask.task.id
    subtask.delete()
    if request.headers.get('HX-Request'):
        response = HttpResponse("")
        response['HX-Trigger'] = 'time-log-updated'
        return response
    return redirect('task_edit', pk=task_id)

# --- CATEGORIES & TAGS ---
@login_required
def category_list_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        color = request.POST.get('color', '#3b82f6')
        attachment = request.FILES.get('attachment')
        if name:
            Category.objects.create(user=request.user, name=name, description=description, color=color, attachment=attachment)
            messages.success(request, "Categoría creada con éxito.")
        return redirect('category_list_create')
        
    categories = Category.objects.filter(user=request.user)
    return render(request, 'categories/category_list.html', {'categories': categories})

@login_required
@require_POST
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    category.delete()
    messages.success(request, "Categoría eliminada.")
    return redirect('category_list_create')

@login_required
def tag_list_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        color = request.POST.get('color', '#ef4444')
        attachment = request.FILES.get('attachment')
        if name:
            Tag.objects.create(user=request.user, name=name, description=description, color=color, attachment=attachment)
            messages.success(request, "Etiqueta creada con éxito.")
        return redirect('tag_list_create')
        
    tags = Tag.objects.filter(user=request.user)
    return render(request, 'tags/tag_list.html', {'tags': tags})

@login_required
@require_POST
def tag_delete(request, pk):
    tag = get_object_or_404(Tag, pk=pk, user=request.user)
    tag.delete()
    messages.success(request, "Etiqueta eliminada.")
    return redirect('tag_list_create')

# --- HTMX TIMER VIEWS ---
@login_required
@require_POST
def start_task_timer(request, task_id):
    # Stop any other active timers for this user first
    TimeLog.objects.filter(user=request.user, end_time__isnull=True).update(end_time=timezone.now())
    # Note: If we stopped another task timer, its status is still IN_PROGRESS but cumulative log works.
    
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.start_timer()
    
    # If the request comes from HTMX, return just the row.
    if request.headers.get('HX-Request'):
        response = render(request, 'tasks/partials/task_row.html', {'task': task})
        response['HX-Trigger'] = 'time-log-updated'
        return response
    return redirect('task_list_create')

@login_required
@require_POST
def stop_task_timer(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.stop_timer()
    if request.headers.get('HX-Request'):
        response = render(request, 'tasks/partials/task_row.html', {'task': task})
        response['HX-Trigger'] = 'time-log-updated'
        return response
    return redirect('task_list_create')

@login_required
@require_POST
def finalize_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.finalize_timer()
    if request.headers.get('HX-Request'):
        response = render(request, 'tasks/partials/task_row.html', {'task': task})
        response['HX-Trigger'] = 'time-log-updated'
        return response
    return redirect('task_list_create')

@login_required
@require_POST
def start_subtask_timer(request, subtask_id):
    TimeLog.objects.filter(user=request.user, end_time__isnull=True).update(end_time=timezone.now())
    subtask = get_object_or_404(Subtask, id=subtask_id, user=request.user)
    subtask.start_timer()
    if request.headers.get('HX-Request'):
        response = render(request, 'tasks/partials/subtask_item.html', {'subtask': subtask})
        response['HX-Trigger'] = 'time-log-updated'
        return response
    return redirect('task_edit', pk=subtask.task.id)

@login_required
@require_POST
def stop_subtask_timer(request, subtask_id):
    subtask = get_object_or_404(Subtask, id=subtask_id, user=request.user)
    subtask.stop_timer()
    if request.headers.get('HX-Request'):
        response = render(request, 'tasks/partials/subtask_item.html', {'subtask': subtask})
        response['HX-Trigger'] = 'time-log-updated'
        return response
    return redirect('task_edit', pk=subtask.task.id)

@login_required
@require_POST
def finalize_subtask(request, subtask_id):
    subtask = get_object_or_404(Subtask, id=subtask_id, user=request.user)
    subtask.finalize_timer()
    if request.headers.get('HX-Request'):
        response = render(request, 'tasks/partials/subtask_item.html', {'subtask': subtask})
        response['HX-Trigger'] = 'time-log-updated'
        return response
    return redirect('task_edit', pk=subtask.task.id)


# --- JSON API ENDPOINTS (For React Kanban & Charts) ---
@login_required
def charts_data_api(request):
    # 1. Pie chart: Time dedicated per project
    projects = Project.objects.filter(user=request.user).prefetch_related('tasks__time_logs')
    pie_data = []
    for project in projects:
        secs = project.total_time_seconds
        if secs > 0:
            pie_data.append({
                'name': project.name,
                'value': round(secs / 3600.0, 2),  # Time in hours
                'seconds': secs
            })
            
    # 2. Bar chart: Time dedicated per Task
    tasks = Task.objects.filter(user=request.user).prefetch_related('time_logs')
    bar_data = []
    for task in tasks:
        secs = task.total_time_seconds
        if secs > 0:
            bar_data.append({
                'name': task.title,
                'value': round(secs / 60.0, 2),  # Time in minutes
                'seconds': secs
            })
            
    # 3. Pie chart: Time dedicated per Category
    categories = Category.objects.filter(user=request.user).prefetch_related('tasks__time_logs')
    category_data = []
    for category in categories:
        secs = 0
        for task in category.tasks.all():
            secs += task.total_time_seconds
        if secs > 0:
            category_data.append({
                'name': category.name,
                'value': round(secs / 3600.0, 2),  # Time in hours
                'seconds': secs,
                'color': category.color
            })

    return JsonResponse({
        'project_times': pie_data,
        'task_times': bar_data,
        'subtask_times': bar_data,
        'category_times': category_data
    })

@login_required
def tasks_api(request):
    tasks = Task.objects.filter(user=request.user).select_related('project', 'category').prefetch_related('tags')
    tasks_list = []
    for task in tasks:
        tasks_list.append({
            'id': task.id,
            'title': task.title,
            'status': task.status,
            'project': task.project.name,
            'category': task.category.name if task.category else None,
            'category_color': task.category.color if task.category else None,
            'tags': [{'name': t.name, 'color': t.color} for t in task.tags.all()],
            'time_spent_secs': task.total_time_seconds,
            'is_running': task.is_running
        })
    return JsonResponse({'tasks': tasks_list})

@login_required
@csrf_exempt  # We can bypass CSRF for this API if verified or read CSRF token
def task_update_status_api(request, task_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            if new_status in ['PENDING', 'IN_PROGRESS', 'COMPLETED']:
                task = get_object_or_404(Task, id=task_id, user=request.user)
                
                # If finalizing, stop timer
                if new_status == 'COMPLETED':
                    task.finalize_timer()
                else:
                    task.status = new_status
                    # If moving away from progress, stop timer but don't mark completed
                    if new_status == 'PENDING' and task.is_running:
                        task.stop_timer()
                    task.save()
                    
                return JsonResponse({'status': 'success', 'task_status': task.status})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
