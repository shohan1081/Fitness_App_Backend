from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from decimal import Decimal
from datetime import timedelta
from health.models import HealthData
from health.utils import calculate_bmr, estimate_met, calculate_calories_for_period

User = get_user_model()

class CalorieCalculationTests(TestCase):
    def setUp(self):
        self.user_male = User.objects.create_user(
            email='male@example.com',
            password='password123',
            full_name='John Doe',
            gender='male',
            age=25,
            current_weight=80,
            height=180,
            height_unit='cm'
        )
        self.user_female = User.objects.create_user(
            email='female@example.com',
            password='password123',
            full_name='Jane Doe',
            gender='female',
            age=25,
            current_weight=60,
            height=165,
            height_unit='cm'
        )

    def test_bmr_calculation(self):
        # Male: (10 * 80) + (6.25 * 180) - (5 * 25) + 5 = 800 + 1125 - 125 + 5 = 1805
        bmr_male = calculate_bmr('male', 80, 180, 25)
        self.assertEqual(bmr_male, Decimal('1805'))

        # Female: (10 * 60) + (6.25 * 165) - (5 * 25) - 161 = 600 + 1031.25 - 125 - 161 = 1345.25
        bmr_female = calculate_bmr('female', 60, 165, 25)
        self.assertEqual(bmr_female, Decimal('1345.25'))

    def test_met_estimation_hr(self):
        # Age 25, Max HR = 195
        # HR 140 is ~71% -> MET 7.0
        self.assertEqual(estimate_met(heart_rate=140, age=25), 7.0)
        # HR 120 is ~61% -> MET 5.0
        self.assertEqual(estimate_met(heart_rate=120, age=25), 5.0)
        # HR 100 is ~51% -> MET 3.0
        self.assertEqual(estimate_met(heart_rate=100, age=25), 3.0)
        # HR 80 is ~41% -> MET 1.0
        self.assertEqual(estimate_met(heart_rate=80, age=25), 1.0)

    def test_met_estimation_steps(self):
        # Step cadence fallback
        self.assertEqual(estimate_met(step_cadence=140), 7.0)
        self.assertEqual(estimate_met(step_cadence=115), 5.0)
        self.assertEqual(estimate_met(step_cadence=90), 3.0)
        self.assertEqual(estimate_met(step_cadence=50), 1.0)

    def test_calorie_period_calculation(self):
        # 10 minutes, Intense activity (MET 7.0)
        # BMR Male = 1805
        # BMR portion = (1805 / 1440) * 10 = 12.5347...
        # Active portion = (7.0 * 3.5 * 80 / 200) * 10 = 9.8 * 10 = 98
        # Total = 110.53
        calories = calculate_calories_for_period(self.user_male, heart_rate=140, step_count=1400, duration_minutes=10)
        self.assertAlmostEqual(float(calories), 110.53, places=1)


class CalorieAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            age=30,
            current_weight=75,
            height=175,
            gender='male'
        )
        self.client.force_authenticate(user=self.user)

    def test_sync_calculates_calories(self):
        # First sync
        response = self.client.post('/api/health/sync/', {
            'heart_rate': 70,
            'step_count': 100,
            'battery_level': 90
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('calories_burned', response.data['data'])
        cal1 = response.data['data']['calories_burned']
        
        # Second sync 10 mins later
        # We need to manually set the recorded_at of the first record to simulate time passing
        first_record = HealthData.objects.first()
        first_record.recorded_at = timezone.now() - timedelta(minutes=10)
        first_record.save()
        
        response = self.client.post('/api/health/sync/', {
            'heart_rate': 120, # Higher HR for more calories
            'step_count': 1200,
            'battery_level': 85
        })
        self.assertEqual(response.status_code, 200)
        cal2 = float(response.data['data']['calories_burned'])
        self.assertGreater(cal2, 0)

    def test_history_endpoint(self):
        # Create some dummy data
        now = timezone.now()
        
        h1 = HealthData.objects.create(user=self.user, calories_burned=10.5, heart_rate=70, step_count=100)
        HealthData.objects.filter(id=h1.id).update(recorded_at=now - timedelta(hours=1))
        
        h2 = HealthData.objects.create(user=self.user, calories_burned=15.0, heart_rate=70, step_count=200)
        HealthData.objects.filter(id=h2.id).update(recorded_at=now - timedelta(hours=2))
        
        # Test 'day' period
        response = self.client.get('/api/health/calories-history/', {'period': 'day'})
        self.assertEqual(response.status_code, 200)
        # Should have at least 2 entries if they fall into different hours
        self.assertTrue(len(response.data['data']) >= 2)
        
        # Test invalid period
        response = self.client.get('/api/health/calories-history/', {'period': 'invalid'})
        self.assertEqual(response.status_code, 400)
