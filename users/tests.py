from django.test import TestCase
from django.urls import reverse
from django.core import mail
from django.contrib.auth import get_user_model
from rest_framework import status
from users.models import ProfileDataDeletionRequest, AccountDeletionRequest
from django.contrib.admin.sites import AdminSite

User = get_user_model()

class PrivacyPolicyTests(TestCase):
    def test_privacy_policy_accessible_without_auth(self):
        """
        Verify that the privacy policy web page can be accessed
        without any authentication/JWT token.
        """
        url = reverse('users:privacy-policy')
        response = self.client.get(url)
        
        # Should render correctly with 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify it uses the correct template
        self.assertTemplateUsed(response, 'users/privacy_policy.html')
        # Check that the body contains essential text
        self.assertContains(response, 'Privacy Policy')
        self.assertContains(response, 'Live More')


class ProfileDeletionWorkflowTests(TestCase):
    def setUp(self):
        # Create a user to delete
        self.user_email = 'delete_me@example.com'
        self.user = User.objects.create_user(
            email=self.user_email,
            password='Password123!',
            full_name='Delete Candidate'
        )
        
        # Create an admin user to trigger the email
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPassword123!'
        )

    def test_profile_deletion_submission_creates_record_but_does_not_email(self):
        """
        Verify that submitting the form registers a pending deletion request
        but does NOT send the email link immediately.
        """
        url = reverse('users:delete-profile-data-request')
        
        # Clear outbox first
        mail.outbox = []
        
        response = self.client.post(url, {'email': self.user_email})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'users/delete_profile_data_submitted.html')
        self.assertContains(response, self.user_email)
        
        # Check database record is created
        request_exists = ProfileDataDeletionRequest.objects.filter(
            email=self.user_email, 
            status='pending'
        ).exists()
        self.assertTrue(request_exists)
        
        # Verify NO email was sent yet (admin must approve first)
        self.assertEqual(len(mail.outbox), 0)

    def test_admin_trigger_sends_deletion_link_and_user_confirmation_deletes_account(self):
        """
        Verify that the admin action triggers the email and that visiting the
        emailed link completes the account deletion.
        """
        # 1. Create the pending request in the DB
        req = ProfileDataDeletionRequest.objects.create(
            user=self.user,
            email=self.user_email,
            status='pending'
        )
        
        # 2. Trigger the admin action programmatically
        from users.admin import ProfileDataDeletionRequestAdmin
        model_admin = ProfileDataDeletionRequestAdmin(ProfileDataDeletionRequest, AdminSite())
        model_admin.message_user = lambda request, message, level=None, extra_tags=None, fail_silently=False: None
        
        # Clear outbox
        mail.outbox = []
        
        # Call the admin action on the queryset
        queryset = ProfileDataDeletionRequest.objects.filter(id=req.id)
        
        # Mock request object for the admin view
        class MockRequest:
            def __init__(self):
                self.META = {'HTTP_HOST': 'testserver'}
            def build_absolute_uri(self, location):
                return f"http://testserver{location}"
        
        mock_request = MockRequest()
        model_admin.send_deletion_link(mock_request, queryset)
        
        # Verify 1 email was sent containing the verification token
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertIn(str(req.verification_token), sent_email.body)
        
        # 3. Simulate user clicking the emailed confirmation link
        confirm_url = reverse(
            'users:verify_profile_data_deletion', 
            kwargs={'token': str(req.verification_token)}
        )
        
        response = self.client.get(confirm_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'users/delete_profile_data_confirmed.html')
        
        # Verify the user is now deleted from the database
        user_exists = User.objects.filter(email=self.user_email).exists()
        self.assertFalse(user_exists)
        
        # Verify the request status in DB is marked as completed
        req.refresh_from_db()
        self.assertEqual(req.status, 'completed')
