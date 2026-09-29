from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
import time
import datetime

from .models import User, Project, Task, Subtask, TimeLog, validate_markdown

class ProjectManagementTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(email="test@user.com", password="password123")
        
        # Create test project
        self.project = Project.objects.create(user=self.user, name="Proyecto Test", description="Descripción Test")
        
    def test_custom_user_creation(self):
        """Verify that the custom user is email-based and uses email as ID."""
        self.assertEqual(self.user.email, "test@user.com")
        self.assertEqual(self.user.pk, "test@user.com")
        
        # Verify USERNAME_FIELD
        self.assertEqual(User.USERNAME_FIELD, 'email')

    def test_markdown_validator(self):
        """Verify that only .md file extensions are allowed."""
        valid_file = SimpleUploadedFile("notes.md", b"some content")
        invalid_file = SimpleUploadedFile("notes.txt", b"some content")
        
        # Should not raise exception
        try:
            validate_markdown(valid_file)
        except ValidationError:
            self.fail("validate_markdown raised ValidationError for a valid .md file")
            
        # Should raise exception
        with self.assertRaises(ValidationError):
            validate_markdown(invalid_file)

    def test_time_tracking_logic(self):
        """Test starting, pausing, and finalizing timers on tasks."""
        task = Task.objects.create(
            user=self.user,
            project=self.project,
            title="Tarea de prueba",
            status="PENDING"
        )
        
        # 1. Start timer
        task.start_timer()
        self.assertTrue(task.is_running)
        self.assertEqual(task.status, "IN_PROGRESS")
        self.assertEqual(task.time_logs.count(), 1)
        
        # 2. Pause/Stop timer
        # Artificially alter start_time in DB to simulate elapsed time
        active_log = task.time_logs.filter(end_time__isnull=True).first()
        active_log.start_time = timezone.now() - datetime.timedelta(seconds=120)
        active_log.save()
        
        task.stop_timer()
        self.assertFalse(task.is_running)
        self.assertEqual(task.total_time_seconds, 120)
        
        # 3. Finalize timer
        task.start_timer() # Start again
        active_log = task.time_logs.filter(end_time__isnull=True).first()
        active_log.start_time = timezone.now() - datetime.timedelta(seconds=30)
        active_log.save()
        
        task.finalize_timer()
        self.assertFalse(task.is_running)
        self.assertEqual(task.status, "COMPLETED")
        # Total time should be 120 + 30 = 150 seconds
        self.assertEqual(task.total_time_seconds, 150)

    def test_subtask_time_tracking_aggregation(self):
        """Verify that starting a subtask timer counts time towards the parent task and project, changes status, and updates charts api."""
        task = Task.objects.create(
            user=self.user,
            project=self.project,
            title="Tarea principal",
            status="PENDING"
        )
        subtask = Subtask.objects.create(
            user=self.user,
            task=task,
            title="Subtarea de prueba",
            is_completed=False
        )
        
        # 1. Start subtask timer
        subtask.start_timer()
        
        # Verify log association
        self.assertTrue(subtask.is_running)
        active_log = subtask.time_logs.filter(end_time__isnull=True).first()
        self.assertIsNotNone(active_log)
        self.assertEqual(active_log.task, task)
        self.assertEqual(active_log.subtask, subtask)
        
        # Verify task status changed to IN_PROGRESS
        task.refresh_from_db()
        self.assertEqual(task.status, "IN_PROGRESS")
        
        # Simulate 300 seconds elapsed
        active_log.start_time = timezone.now() - datetime.timedelta(seconds=300)
        active_log.save()
        
        # Stop subtask timer
        subtask.stop_timer()
        self.assertFalse(subtask.is_running)
        
        # Verify time is reflected in task and project
        self.assertEqual(subtask.total_time_seconds, 300)
        self.assertEqual(task.total_time_seconds, 300)
        self.assertEqual(self.project.total_time_seconds, 300)
        
        # Verify charts API output
        self.client.force_login(self.user)
        response = self.client.get('/api/dashboard/charts-data/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check task_times exists and contains the correct consolidated task time in minutes
        self.assertIn('task_times', data)
        task_data = next((item for item in data['task_times'] if item['name'] == task.title), None)
        self.assertIsNotNone(task_data)
        self.assertEqual(task_data['value'], 5.0) # 300s = 5m

    def test_subtask_description_field(self):
        """Verify subtasks can store a markdown description."""
        task = Task.objects.create(user=self.user, project=self.project, title="Tarea con subtarea")
        subtask = Subtask.objects.create(
            user=self.user,
            task=task,
            title="Subtarea con notas",
            description="# Notas\nAlgo de contenido",
        )
        self.assertEqual(subtask.description, "# Notas\nAlgo de contenido")

    def test_task_detail_page(self):
        """Verify the detail page shows the task description and its subtasks with descriptions."""
        task = Task.objects.create(
            user=self.user,
            project=self.project,
            title="Tarea detalle",
            description="# Descripción\nContenido de la tarea",
        )
        Subtask.objects.create(
            user=self.user,
            task=task,
            title="Subtarea 1",
            description="## Nota de la subtarea",
        )
        self.client.force_login(self.user)
        response = self.client.get(f'/tasks/{task.id}/detail/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("# Descripción", html)  # raw markdown rendered via data-markdown
        self.assertIn("Contenido de la tarea", html)
        self.assertIn("Subtarea 1", html)
        self.assertIn("## Nota de la subtarea", html)

    def test_task_list_hides_description_and_shows_note_icon(self):
        """Verify the task list does not render the description inline but links to the detail page."""
        task = Task.objects.create(
            user=self.user,
            project=self.project,
            title="Tarea con notas",
            description="# Notas\nNo debe verse en la lista",
        )
        self.client.force_login(self.user)
        response = self.client.get('/tasks/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        # Description must not be rendered inline in the list
        self.assertNotIn("No debe verse en la lista", html)
        self.assertNotIn('data-markdown=', html)
        # Note icon linking to the detail page must be present
        self.assertIn(f'/tasks/{task.id}/detail/', html)
        self.assertIn("fa-note-sticky", html)

    def test_calendar_view_invalid_params_does_not_500(self):
        """Verify calendar_view safely handles invalid year/month query params without throwing 500."""
        self.client.force_login(self.user)
        # Non-numeric query params
        res = self.client.get('/calendar/?year=invalid&month=99')
        self.assertEqual(res.status_code, 200)
        self.assertIn("Calendario de Tareas", res.content.decode())

        # Negative / zero month
        res2 = self.client.get('/calendar/?year=2026&month=0')
        self.assertEqual(res2.status_code, 200)

    def test_safe_project_cascade_delete(self):
        """Verify that deleting a Project with tasks does not raise DoesNotExist."""
        project2 = Project.objects.create(user=self.user, name="Proyecto Cascada")
        Task.objects.create(user=self.user, project=project2, title="Tarea 1")
        Task.objects.create(user=self.user, project=project2, title="Tarea 2")
        
        # Deleting project should succeed cleanly
        project2.delete()
        self.assertEqual(Project.objects.filter(id=project2.id).count(), 0)

    def test_subtask_total_time_formatted(self):
        """Verify total_time_formatted property on Subtask."""
        task = Task.objects.create(user=self.user, project=self.project, title="Tarea Subtask Time")
        subtask = Subtask.objects.create(user=self.user, task=task, title="Subtarea Time")
        self.assertEqual(subtask.total_time_formatted, "00:00:00")

    def test_task_edit_updates_status(self):
        """Verify that editing a task updates its status and project status."""
        task = Task.objects.create(user=self.user, project=self.project, title="Tarea Status Edit", status="PENDING")
        self.client.force_login(self.user)
        res = self.client.post(f'/tasks/{task.id}/edit/', {
            'title': 'Tarea Status Edit Updated',
            'project': self.project.id,
            'status': 'COMPLETED'
        })
        self.assertEqual(res.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.status, 'COMPLETED')
        self.assertEqual(task.title, 'Tarea Status Edit Updated')

    def test_task_update_status_api(self):
        """Verify task_update_status_api works via POST."""
        task = Task.objects.create(user=self.user, project=self.project, title="Tarea API Status", status="PENDING")
        self.client.force_login(self.user)
        res = self.client.post(
            f'/api/tasks/{task.id}/update-status/',
            data='{"status": "IN_PROGRESS"}',
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get('task_status'), 'IN_PROGRESS')
        task.refresh_from_db()
        self.assertEqual(task.status, 'IN_PROGRESS')

