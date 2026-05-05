from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import HealthData, Workout, WeightLog
from .serializers import HealthDataSerializer, WorkoutSerializer, WeightLogSerializer

def standard_response(success=True, message="", data=None, errors=None, status_code=status.HTTP_200_OK):
    """
    Create standardized API response (replicated from users app for consistency)
    """
    response_data = {
        'success': success,
        'message': message,
    }
    if data is not None:
        response_data['data'] = data
    if errors is not None:
        response_data['errors'] = errors
    return Response(response_data, status=status_code)

class HealthDataUpdateView(APIView):
    """
    API for Flutter to sync health data (heart rate, steps, battery, etc.)
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = HealthDataSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return standard_response(success=True, message="Health data synced", data=serializer.data)
        return standard_response(success=False, errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

class UserDashboardView(APIView):
    """
    Dashboard API providing consolidated health and fitness metrics.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        
        # Latest health metrics
        latest_health = HealthData.objects.filter(user=user).first()
        
        # Calculate BMI
        bmi = None
        if user.height and user.current_weight:
            height_m = float(user.height) / 100.0 if user.height_unit == 'cm' else float(user.height) * 0.3048
            bmi = round(float(user.current_weight) / (height_m ** 2), 2)
        
        # Weight difference
        weight_diff = None
        if user.current_weight and user.goal_weight:
            weight_diff = round(float(user.goal_weight) - float(user.current_weight), 2)
            
        # Recent Workouts
        recent_workouts = Workout.objects.filter(user=user)[:5]
        workout_serializer = WorkoutSerializer(recent_workouts, many=True)

        dashboard_data = {
            'user_name': f"{user.first_name} {user.last_name}".strip() or user.email,
            'heart_rate': latest_health.heart_rate if latest_health else None,
            'step_count': latest_health.step_count if latest_health else 0,
            'calories_today': latest_health.calories_burned if latest_health else 0,
            'battery_level': latest_health.battery_level if latest_health else None,
            'current_bmi': bmi,
            'current_weight': user.current_weight,
            'goal_weight': user.goal_weight,
            'weight_difference': weight_diff,
            'recent_workouts': workout_serializer.data
        }

        return standard_response(success=True, message="Dashboard data retrieved", data=dashboard_data)

class UserBMIView(APIView):
    """
    API to retrieve detailed BMI information for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        if not user.height or not user.current_weight:
            return standard_response(
                success=False, 
                message="Height and weight information are required to calculate BMI.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Calculate BMI
        try:
            height_m = float(user.height) / 100.0 if user.height_unit == 'cm' else float(user.height) * 0.3048
            bmi = round(float(user.current_weight) / (height_m ** 2), 2)
        except (ValueError, ZeroDivisionError, TypeError):
            return standard_response(
                success=False,
                message="Invalid height or weight data.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Determine category and message
        if bmi < 18.5:
            category, label = "Underweight", "underweight"
            message = "You are in the underweight range. It's important to consume enough nutrients and consult with a healthcare provider or nutritionist for a healthy weight gain plan."
        elif 18.5 <= bmi < 25:
            category, label = "Normal weight", "normal"
            message = "You are in a healthy range. Maintain your current weight with regular exercise and a balanced diet to stay on track."
        elif 25 <= bmi < 30:
            category, label = "Overweight", "overweight"
            message = "You are in the overweight range. Incorporating more physical activity and focusing on a balanced, calorie-controlled diet can help you reach a healthier weight."
        else:
            category, label = "Obesity", "obesity"
            message = "You are in the obesity range. We recommend consulting with a healthcare professional to develop a safe and effective plan for weight management and overall health."

        bmi_data = {
            'current_bmi': bmi,
            'category': category,
            'label': label,
            'message': message,
            'scale': [
                {'label': 'Underweight', 'range': 'Below 18.5'},
                {'label': 'Normal weight', 'range': '18.5 - 24.9'},
                {'label': 'Overweight', 'range': '25.0 - 29.9'},
                {'label': 'Obesity', 'range': '30.0 or greater'}
            ]
        }

        return standard_response(success=True, message="BMI details retrieved successfully", data=bmi_data)


class WeightLogUpdateView(APIView):
    """
    API to log or update user weight.
    Updates the main User model's current_weight and creates a history log.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = WeightLogSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            # Save weight log entry
            weight_log = serializer.save(user=request.user)
            
            # Also update the current_weight in User model
            user = request.user
            user.current_weight = weight_log.weight
            user.save(update_fields=['current_weight'])
            
            return standard_response(
                success=True, 
                message="Weight updated successfully", 
                data=serializer.data
            )
        return standard_response(
            success=False, 
            message="Validation failed", 
            errors=serializer.errors, 
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def get(self, request):
        """Retrieve weight history"""
        logs = WeightLog.objects.filter(user=request.user)
        serializer = self.serializer_class(logs, many=True)
        return standard_response(success=True, data=serializer.data)
