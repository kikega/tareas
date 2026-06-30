import os
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.utils import timezone

def validate_markdown(value):
    ext = os.path.splitext(value.name)[1]
    if ext.lower() != '.md':
        raise ValidationError("Únicamente se permiten archivos en formato Markdown (.md).")

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El correo electrónico es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(primary_key=True, unique=True, verbose_name="Correo Electrónico")
    first_name = models.CharField(max_length=150, blank=True, verbose_name="Nombre")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="Apellidos")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_staff = models.BooleanField(default=False, verbose_name="Staff")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.email

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción (Markdown)")
    color = models.CharField(max_length=7, default="#3b82f6", verbose_name="Color Hex")
    attachment = models.FileField(upload_to='categories/markdown/', blank=True, null=True, validators=[validate_markdown], verbose_name="Adjunto Markdown")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.name

class Tag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción (Markdown)")
    color = models.CharField(max_length=7, default="#ef4444", verbose_name="Color Hex")
    attachment = models.FileField(upload_to='tags/markdown/', blank=True, null=True, validators=[validate_markdown], verbose_name="Adjunto Markdown")

    class Meta:
        verbose_name = "Etiqueta"
        verbose_name_plural = "Etiquetas"

    def __str__(self):
        return self.name

class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200, verbose_name="Nombre del Proyecto")
    description = models.TextField(blank=True, verbose_name="Descripción")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return self.name

    @property
    def total_time_seconds(self):
        total = 0
        for task in self.tasks.all():
            total += task.total_time_seconds
        return total

class Task(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('IN_PROGRESS', 'En Progreso'),
        ('COMPLETED', 'Completada'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    tags = models.ManyToManyField(Tag, blank=True, related_name='tasks')
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(blank=True, verbose_name="Descripción (Markdown)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Estado")
    attachment = models.FileField(upload_to='tasks/markdown/', blank=True, null=True, validators=[validate_markdown], verbose_name="Adjunto (.md)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', '-updated_at']),
        ]

    def __str__(self):
        return self.title

    @property
    def total_time_seconds(self):
        total_secs = 0
        for log in self.time_logs.all():
            if log.end_time:
                total_secs += int((log.end_time - log.start_time).total_seconds())
            else:
                total_secs += int((timezone.now() - log.start_time).total_seconds())
        return total_secs

    @property
    def is_running(self):
        if 'time_logs' in getattr(self, '_prefetched_objects_cache', {}):
            return any(log.end_time is None for log in self.time_logs.all())
        return self.time_logs.filter(end_time__isnull=True).exists()

    def start_timer(self):
        if not self.is_running:
            self.status = 'IN_PROGRESS'
            self.save()
            TimeLog.objects.create(user=self.user, task=self, start_time=timezone.now())

    def stop_timer(self):
        active_log = self.time_logs.filter(end_time__isnull=True).first()
        if active_log:
            active_log.end_time = timezone.now()
            active_log.save()

    def finalize_timer(self):
        self.stop_timer()
        self.status = 'COMPLETED'
        self.save()

    @property
    def completed_subtasks_count(self):
        if 'subtasks' in getattr(self, '_prefetched_objects_cache', {}):
            return sum(1 for s in self.subtasks.all() if s.is_completed)
        return self.subtasks.filter(is_completed=True).count()

    @property
    def total_subtasks_count(self):
        if 'subtasks' in getattr(self, '_prefetched_objects_cache', {}):
            return len(self.subtasks.all())
        return self.subtasks.count()

class Subtask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subtasks')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=200, verbose_name="Título")
    is_completed = models.BooleanField(default=False, verbose_name="Completada")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Subtarea"
        verbose_name_plural = "Subtareas"

    def __str__(self):
        return self.title

    @property
    def total_time_seconds(self):
        total_secs = 0
        for log in self.time_logs.all():
            if log.end_time:
                total_secs += int((log.end_time - log.start_time).total_seconds())
            else:
                total_secs += int((timezone.now() - log.start_time).total_seconds())
        return total_secs

    @property
    def is_running(self):
        if 'time_logs' in getattr(self, '_prefetched_objects_cache', {}):
            return any(log.end_time is None for log in self.time_logs.all())
        return self.time_logs.filter(end_time__isnull=True).exists()

    def start_timer(self):
        if not self.is_running:
            if self.task.status == 'PENDING':
                self.task.status = 'IN_PROGRESS'
                self.task.save()
            TimeLog.objects.create(user=self.user, subtask=self, task=self.task, start_time=timezone.now())

    def stop_timer(self):
        active_log = self.time_logs.filter(end_time__isnull=True).first()
        if active_log:
            active_log.end_time = timezone.now()
            active_log.save()

    def finalize_timer(self):
        self.stop_timer()
        self.is_completed = True
        self.save()

class TimeLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_logs')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True, related_name='time_logs')
    subtask = models.ForeignKey(Subtask, on_delete=models.CASCADE, null=True, blank=True, related_name='time_logs')
    start_time = models.DateTimeField(verbose_name="Inicio")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="Fin")

    class Meta:
        verbose_name = "Registro de Tiempo"
        verbose_name_plural = "Registros de Tiempo"
        indexes = [
            models.Index(fields=['user', '-start_time']),
            models.Index(fields=['user', 'end_time']),
        ]

    @property
    def duration_seconds(self):
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds())
        return int((timezone.now() - self.start_time).total_seconds())

    @property
    def duration_formatted(self):
        secs = self.duration_seconds
        h = secs // 3600
        m = (secs % 3600) // 60
        s = secs % 60
        if h > 0:
            return f"{h}h {m}m"
        if m > 0:
            return f"{m}m {s}s"
        return f"{s}s"
