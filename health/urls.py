from django.urls import path
from .views import (
    HealthDataUpdateView,
    UserDashboardView,
    UserBMIView,
    WeightLogUpdateView,
)

app_name = 'health'

urlpatterns = [
    path('sync/', HealthDataUpdateView.as_view(), name='health-sync'),
    path('dashboard/', UserDashboardView.as_view(), name='dashboard'),
    path('bmi/', UserBMIView.as_view(), name='bmi-details'),
    path('weight-update/', WeightLogUpdateView.as_view(), name='weight-update'),
]
