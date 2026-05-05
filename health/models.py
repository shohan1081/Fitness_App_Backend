from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class HealthData(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='health_records'
    )
    heart_rate = models.IntegerField(_('heart rate'), null=True, blank=True)
    step_count = models.IntegerField(_('step count'), default=0)
    calories_burned = models.DecimalField(_('calories burned'), max_digits=7, decimal_places=2, default=0.0)
    battery_level = models.IntegerField(_('device battery level'), null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('health data')
        verbose_name_plural = _('health data records')
        ordering = ['-recorded_at']

class Workout(models.Model):
    WORKOUT_TYPES = [
        ('running', 'Running'),
        ('walking', 'Walking'),
        ('cycling', 'Cycling'),
        ('gym', 'Gym/Strength'),
        ('yoga', 'Yoga'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='workouts'
    )
    workout_type = models.CharField(max_length=50, choices=WORKOUT_TYPES)
    duration_minutes = models.IntegerField()
    calories_burned = models.DecimalField(max_digits=7, decimal_places=2)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']


class WeightLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='weight_logs'
    )
    weight = models.DecimalField(_('weight'), max_digits=5, decimal_places=2)
    date = models.DateField(_('date'), default=timezone.now)
    notes = models.TextField(_('notes'), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('weight log')
        verbose_name_plural = _('weight logs')
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.weight}kg on {self.date}"
