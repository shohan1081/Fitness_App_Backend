from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import TruncHour, TruncDay, TruncMonth

from .models import HealthData, Workout, WeightLog
from .serializers import (
    HealthDataSerializer, WorkoutSerializer, WeightLogSerializer,
    WorkoutStartSerializer, WorkoutFinishSerializer
)
from .utils import calculate_calories_for_period, get_bmi_info

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
        user = request.user
        data = request.data.copy()
        
        # Get heart rate and steps from request
        heart_rate = data.get('heart_rate')
        if heart_rate is not None:
            try:
                heart_rate = int(heart_rate)
            except (ValueError, TypeError):
                heart_rate = None
        
        current_steps = int(data.get('step_count', 0))
        
        # Find last sync to calculate duration and steps in period
        last_sync = HealthData.objects.filter(user=user).order_by('-recorded_at').first()
        
        if last_sync:
            # Time difference in minutes
            time_diff = (timezone.now() - last_sync.recorded_at).total_seconds() / 60
            
            # If it's a new day, or steps were reset, steps_in_period is just current_steps
            # Otherwise it's the difference
            if last_sync.recorded_at.date() < timezone.now().date():
                steps_in_period = current_steps
            else:
                steps_in_period = max(0, current_steps - last_sync.step_count)
            
            duration_minutes = time_diff
        else:
            # First sync ever or for a long time - assume small default duration or just active
            duration_minutes = 5
            steps_in_period = current_steps

        # Calculate calories
        calories = calculate_calories_for_period(
            user, 
            heart_rate, 
            steps_in_period, 
            duration_minutes
        )
        
        # Override or set calories_burned in the data
        data['calories_burned'] = float(calories)

        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save(user=user)
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

        # Get BMI info
        bmi_info = get_bmi_info(bmi)

        dashboard_data = {
            'user_name': user.full_name or user.email,
            'heart_rate': latest_health.heart_rate if latest_health else None,
            'step_count': latest_health.step_count if latest_health else 0,
            'calories_today': latest_health.calories_burned if latest_health else 0,
            'battery_level': latest_health.battery_level if latest_health else None,
            'current_bmi': bmi,
            'current_bmi_level': bmi_info['category'] if bmi_info else None,
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

        # Use utility for category and message
        bmi_data = get_bmi_info(bmi)
        bmi_data['current_bmi'] = bmi

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

class CalorieHistoryView(APIView):
    """
    API to retrieve aggregated calorie burn history for progress bars.
    Supports period=day, week, month, year.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        period = request.query_params.get('period', 'day')
        user = request.user
        
        # Base queryset
        queryset = HealthData.objects.filter(user=user)
        
        if period == 'day':
            # Hourly record for today
            queryset = queryset.filter(recorded_at__date=timezone.now().date()) \
                               .annotate(time_label=TruncHour('recorded_at'))
        elif period == 'week':
            # Daily record for last 7 days
            start_date = timezone.now().date() - timezone.timedelta(days=7)
            queryset = queryset.filter(recorded_at__date__gte=start_date) \
                               .annotate(time_label=TruncDay('recorded_at'))
        elif period == 'month':
            # Daily record for current month
            queryset = queryset.filter(recorded_at__month=timezone.now().month, 
                                       recorded_at__year=timezone.now().year) \
                               .annotate(time_label=TruncDay('recorded_at'))
        elif period == 'year':
            # Monthly record for current year
            queryset = queryset.filter(recorded_at__year=timezone.now().year) \
                               .annotate(time_label=TruncMonth('recorded_at'))
        else:
            return standard_response(success=False, message="Invalid period", status_code=status.HTTP_400_BAD_REQUEST)
        
        # Group and Sum
        history_data = queryset.values('time_label') \
                               .annotate(total_calories=Sum('calories_burned')) \
                               .order_by('time_label')
        
        # Format labels for Flutter charts and calculate statistics
        formatted_data = []
        total_calories = 0
        highest_calories = 0
        
        for item in history_data:
            if not item['time_label']:
                continue
                
            label = ""
            if period == 'day':
                label = item['time_label'].strftime('%H:00')
            elif period in ['week', 'month']:
                label = item['time_label'].strftime('%Y-%m-%d')
            elif period == 'year':
                label = item['time_label'].strftime('%Y-%m')
            
            calories = round(float(item['total_calories']), 2)
            
            # Update statistics
            total_calories += calories
            if calories > highest_calories:
                highest_calories = calories
                
            formatted_data.append({
                'label': label,
                'calories': calories
            })
        
        # Calculate average
        average_calories = 0
        if len(formatted_data) > 0:
            average_calories = round(total_calories / len(formatted_data), 2)
            
        # Recent Workouts for the summary
        recent_workouts = Workout.objects.filter(
            user=user, 
            is_active=False,
            completed_at__date=timezone.now().date()
        ).order_by('-completed_at')
        workout_serializer = WorkoutSerializer(recent_workouts, many=True)

        response_data = {
            'total_calories': round(total_calories, 2),
            'highest_calories': highest_calories,
            'average_calories': average_calories,
            'recent_workouts': workout_serializer.data,
            'chart_data': formatted_data
        }
            
        return standard_response(success=True, data=response_data)

class StartWorkoutView(APIView):
    """
    API to start a new workout session.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = WorkoutStartSerializer

    def post(self, request):
        # Close any existing active workouts for this user
        Workout.objects.filter(user=request.user, is_active=True).update(
            is_active=False, 
            end_time=timezone.now()
        )
        
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            # Extract non-model fields
            start_steps = serializer.validated_data.pop('step_count')
            avg_heart_rate = serializer.validated_data.pop('heart_rate')
            
            workout = serializer.save(
                user=request.user,
                is_active=True,
                start_time=timezone.now(),
                start_steps=start_steps,
                avg_heart_rate=avg_heart_rate
            )
            return standard_response(
                success=True, 
                message=f"{workout.get_workout_type_display()} session started", 
                data=WorkoutSerializer(workout).data
            )
        return standard_response(success=False, errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

class FinishWorkoutView(APIView):
    """
    API to finish an active workout session and calculate results.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = WorkoutFinishSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return standard_response(success=False, errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        
        try:
            workout = Workout.objects.get(
                id=serializer.validated_data['workout_id'], 
                user=request.user, 
                is_active=True
            )
        except Workout.DoesNotExist:
            return standard_response(success=False, message="Active workout not found", status_code=status.HTTP_404_NOT_FOUND)
        
        # Calculate or use provided results
        end_time = serializer.validated_data.get('date') or timezone.now()
        
        duration_minutes = serializer.validated_data.get('duration_minutes')
        if not duration_minutes:
            duration_delta = end_time - workout.start_time
            duration_minutes = max(1, int(duration_delta.total_seconds() / 60))
        
        end_steps = serializer.validated_data['step_count']
        steps_in_workout = max(0, end_steps - workout.start_steps)
        
        heart_rate = serializer.validated_data.get('heart_rate') or workout.avg_heart_rate
        
        # Use common utility for calories
        calories = calculate_calories_for_period(
            request.user, 
            heart_rate, 
            steps_in_workout, 
            duration_minutes
        )
        
        # Update workout record
        workout.is_active = False
        workout.end_time = end_time
        workout.end_steps = end_steps
        workout.duration_minutes = duration_minutes
        workout.calories_burned = calories
        if serializer.validated_data.get('heart_rate'):
            workout.avg_heart_rate = (workout.avg_heart_rate + heart_rate) // 2
        workout.save()
        
        return standard_response(
            success=True, 
            message="Workout completed", 
            data=WorkoutSerializer(workout).data
        )

class WorkoutStatsView(APIView):
    """
    API to retrieve weekly workout statistics.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        # Start of 7 days ago (midnight)
        start_date = (timezone.now() - timezone.timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Base weekly queryset
        weekly_workouts = Workout.objects.filter(
            user=user, 
            is_active=False,
            completed_at__gte=start_date
        )
        
        # Basic aggregates
        total_sessions = weekly_workouts.count()
        aggregates = weekly_workouts.aggregate(
            total_duration=Sum('duration_minutes'),
            total_calories=Sum('calories_burned')
        )
        
        total_duration = aggregates['total_duration'] or 0
        total_calories = float(aggregates['total_calories'] or 0.0)
        
        # Average duration
        average_duration = round(total_duration / total_sessions, 2) if total_sessions > 0 else 0
        
        # Best day session count and Chart data (calories per day)
        daily_stats = {}
        # Pre-fill last 7 days with 0s to ensure consistent chart labels
        for i in range(7):
            day = (timezone.now() - timezone.timedelta(days=i)).date()
            daily_stats[day] = {'sessions': 0, 'calories': 0.0}
            
        for workout in weekly_workouts:
            day = workout.completed_at.date()
            if day in daily_stats:
                daily_stats[day]['sessions'] += 1
                daily_stats[day]['calories'] += float(workout.calories_burned or 0.0)
        
        best_day_session_count = max([day['sessions'] for day in daily_stats.values()]) if daily_stats else 0
        
        # Format chart data (sorted by date)
        chart_data = []
        for day in sorted(daily_stats.keys()):
            chart_data.append({
                'label': day.strftime('%Y-%m-%d'),
                'calories': round(daily_stats[day]['calories'], 2)
            })
            
        # Weekly history
        history = WorkoutSerializer(weekly_workouts.order_by('-completed_at'), many=True).data
        
        stats_data = {
            'total_sessions': total_sessions,
            'total_duration_minutes': total_duration,
            'total_calories_burned': round(total_calories, 2),
            'average_duration_minutes': average_duration,
            'best_day_session_count': best_day_session_count,
            'chart_data': chart_data,
            'history': history
        }
        
        return standard_response(success=True, data=stats_data)
