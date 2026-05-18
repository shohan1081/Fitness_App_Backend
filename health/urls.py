from django.urls import path
from .views import (
    HealthDataUpdateView,
    UserDashboardView,
    UserBMIView,
    WeightLogUpdateView,
    CalorieHistoryView,
    StartWorkoutView,
    FinishWorkoutView,
    WorkoutStatsView,
)

app_name = 'health'

urlpatterns = [
    path('sync/', HealthDataUpdateView.as_view(), name='health-sync'),
    path('dashboard/', UserDashboardView.as_view(), name='dashboard'),
    path('bmi/', UserBMIView.as_view(), name='bmi-details'),
    path('weight-update/', WeightLogUpdateView.as_view(), name='weight-update'),
    path('calories-history/', CalorieHistoryView.as_view(), name='calories-history'),
    path('workout/start/', StartWorkoutView.as_view(), name='workout-start'),
    path('workout/finish/', FinishWorkoutView.as_view(), name='workout-finish'),
    path('workout/stats/', WorkoutStatsView.as_view(), name='workout-stats'),
]
