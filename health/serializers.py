from rest_framework import serializers
from .models import HealthData, Workout, WeightLog

class HealthDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthData
        fields = ['heart_rate', 'step_count', 'calories_burned', 'battery_level', 'recorded_at']
        read_only_fields = ['recorded_at']

class WorkoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workout
        fields = ['id', 'workout_type', 'duration_minutes', 'calories_burned', 'completed_at']
        read_only_fields = ['completed_at']

class WeightLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightLog
        fields = ['id', 'weight', 'date', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']
