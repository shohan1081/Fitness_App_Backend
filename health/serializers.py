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
        fields = [
            'id', 'workout_type', 'is_active', 'start_time', 'end_time', 
            'start_steps', 'end_steps', 'avg_heart_rate', 
            'duration_minutes', 'calories_burned', 'completed_at'
        ]
        read_only_fields = ['completed_at']

class WorkoutStartSerializer(serializers.ModelSerializer):
    heart_rate = serializers.IntegerField(required=True, write_only=True)
    step_count = serializers.IntegerField(required=True, write_only=True)

    class Meta:
        model = Workout
        fields = ['workout_type', 'heart_rate', 'step_count']

class WorkoutFinishSerializer(serializers.Serializer):
    workout_id = serializers.IntegerField(required=True)
    heart_rate = serializers.IntegerField(required=False)
    step_count = serializers.IntegerField(required=True)
    duration_minutes = serializers.IntegerField(required=False)
    date = serializers.DateTimeField(required=False)

class WeightLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightLog
        fields = ['id', 'weight', 'date', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']
