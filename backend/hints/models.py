from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Problem(models.Model):
    id = models.AutoField(primary_key=True)  # Explicitly define integer ID
    title = models.CharField(max_length=200)
    description = models.TextField()  # Raw problem statement
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}: {self.title}"

class UserProgress(models.Model):
    user_id = models.IntegerField()
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='user_progress')
    last_activity = models.DateTimeField(auto_now=True)
    attempts_count = models.IntegerField(default=0)
    failed_attempts_count = models.IntegerField(default=0)
    current_hint_level = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_stuck(self):
        """Check if user is stuck based on inactivity and failed attempts"""
        time_threshold = timedelta(minutes=5)
        return (
            timezone.now() - self.last_activity > time_threshold and
            self.failed_attempts_count >= 3
        )

    def __str__(self):
        return f"Progress for user {self.user_id} on {self.problem.title}"

class Attempt(models.Model):
    user_id = models.IntegerField()  # Using integer for user_id as we don't have auth
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='attempts')
    code = models.TextField()
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attempt by user {self.user_id} on {self.problem.title}"

class Hint(models.Model):
    HINT_TYPES = [
        ('conceptual', 'Conceptual'),
        ('approach', 'Approach'),
        ('implementation', 'Implementation'),
        ('debug', 'Debug')
    ]

    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='hints')
    content = models.TextField()
    level = models.IntegerField(default=1)
    hint_type = models.CharField(max_length=20, choices=HINT_TYPES, default='conceptual')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Hint {self.level} for {self.problem.title}"

class HintDelivery(models.Model):
    hint = models.ForeignKey(Hint, on_delete=models.CASCADE, related_name='deliveries')
    user_id = models.IntegerField()
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='hint_deliveries')
    is_auto_triggered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Hint delivery to user {self.user_id}"

class HintEvaluation(models.Model):
    hint = models.ForeignKey(Hint, on_delete=models.CASCADE, related_name='evaluations')
    safety_score = models.FloatField(default=0)
    helpfulness_score = models.FloatField(default=0)
    quality_score = models.FloatField(default=0)
    progress_alignment_score = models.FloatField(default=0)
    pedagogical_value_score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evaluation for hint {self.hint.id}"
