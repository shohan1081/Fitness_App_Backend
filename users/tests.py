from django.test import TestCase
from django.urls import reverse
from rest_framework import status

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
