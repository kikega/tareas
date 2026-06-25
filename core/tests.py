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
