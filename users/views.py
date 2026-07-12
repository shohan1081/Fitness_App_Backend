from django.shortcuts import render
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Q as DjangoQ

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetOTPVerifySerializer,
    ResendOTPSerializer,
    VerifyOTPSerializer,
    PasswordChangeSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    AccountDeleteSerializer,
    UserFitnessInfoSerializer,
    SupportTicketSerializer,
    PublicUserProfileSerializer,
)
from .utils import (
    send_welcome_email,
    send_account_deletion_email,
    get_client_ip,
    get_user_agent,
    get_full_media_url,
)
from .models import (
    UserLoginHistory, 
    AccountDeletionRequest, 
    ProfileDataDeletionRequest
)

User = get_user_model()

def standard_response(success=True, message="", data=None, errors=None, status_code=status.HTTP_200_OK):
    """
    Create standardized API response
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

class SupportTicketView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = SupportTicketSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email_address = serializer.validated_data['email_address']
            subject = serializer.validated_data['subject']
            message = serializer.validated_data['message']
            admin_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'admin@example.com')
            email_subject = f"Support Request: {subject}"
            email_message = f"From: {email_address}\n\nMessage:\n{message}"
            try:
                send_mail(email_subject, email_message, settings.DEFAULT_FROM_EMAIL, [admin_email], fail_silently=False)
                return standard_response(success=True, message="Support request sent successfully.")
            except Exception as e:
                return standard_response(success=False, message=f"Failed: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return standard_response(success=False, message="Invalid data", errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

class UserRegistrationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = UserRegistrationSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return standard_response(success=True, message="OTP sent.", data={'user': {'id': str(user.id), 'email': user.email}}, status_code=status.HTTP_201_CREATED)
        return standard_response(success=False, message="Failed", errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = UserLoginSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            UserLoginHistory.objects.create(user=user, ip_address=get_client_ip(request), user_agent=get_user_agent(request))
            return standard_response(success=True, message="Login successful", data={
                'account_type': 'personal',
                'user': {'id': str(user.id), 'email': user.email, 'profile_picture': get_full_media_url(request, user.profile_picture)},
                'tokens': {'access': str(refresh.access_token), 'refresh': str(refresh)}
            })
        return standard_response(success=False, message="Login failed", errors=serializer.errors, status_code=status.HTTP_401_UNAUTHORIZED)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def get(self, request):
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return standard_response(success=True, data=serializer.data)
    def patch(self, request):
        serializer = UserProfileUpdateSerializer(request.user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return standard_response(success=True, message="Profile updated", data=UserProfileSerializer(request.user, context={'request': request}).data)
        return standard_response(success=False, message="Failed", errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    def put(self, request):
        return self.patch(request)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = VerifyOTPSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email, otp = serializer.validated_data['email'], serializer.validated_data['otp']
            try:
                user = User.objects.get(email=email)
                if user.otp == otp and user.is_otp_valid():
                    user.is_active = True
                    user.is_email_verified = True
                    user.clear_otp()
                    user.save()
                    refresh = RefreshToken.for_user(user)
                    return standard_response(success=True, message="OTP verified", data={
                        'account_type': 'personal',
                        'user': {'id': str(user.id), 'email': user.email, 'profile_picture': get_full_media_url(request, user.profile_picture)},
                        'tokens': {'access': str(refresh.access_token), 'refresh': str(refresh)}
                    })
                return standard_response(success=False, message="Invalid OTP", status_code=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist: return standard_response(success=False, message="User not found", status_code=status.HTTP_404_NOT_FOUND)
        return standard_response(success=False, errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ResendOTPSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(email=serializer.validated_data['email'])
                from .utils import generate_otp, send_otp_email
                otp = generate_otp()
                user.otp, user.otp_created_at = otp, timezone.now()
                user.save()
                send_otp_email(user, otp)
                return standard_response(success=True, message="OTP resent.")
            except User.DoesNotExist: return standard_response(success=False, message="Not found", status_code=status.HTTP_404_NOT_FOUND)
        return standard_response(success=False, errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = PasswordResetRequestSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email'].lower()
            user = User.objects.filter(email=email).first()
            if user:
                from .utils import generate_otp, send_otp_email
                otp = generate_otp()
                user.otp, user.otp_created_at = otp, timezone.now()
                user.save()
                send_otp_email(user, otp)
            return standard_response(success=True, message="If email exists, OTP sent.")
        return standard_response(success=False, errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

class PasswordResetOTPVerifyView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = PasswordResetOTPVerifySerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email, otp = serializer.validated_data['email'].lower(), serializer.validated_data['otp']
            user = User.objects.filter(email=email).first()
            if user and user.otp == otp and user.is_otp_valid():
                user.clear_otp()
                return standard_response(success=True, message="OTP verified.")
            return standard_response(success=False, message="Invalid OTP", status_code=status.HTTP_400_BAD_REQUEST)
        return standard_response(success=False, errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = PasswordResetConfirmSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email, pwd = serializer.validated_data['email'].lower(), serializer.validated_data['password']
            user = User.objects.filter(email=email).first()
            if user:
                user.set_password(pwd)
                user.save()
                return standard_response(success=True, message="Password reset success.")
            return standard_response(success=False, message="Not found", status_code=status.HTTP_404_NOT_FOUND)
        return standard_response(success=False, errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = PasswordChangeSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            if not request.user.check_password(serializer.validated_data['old_password']):
                return standard_response(success=False, message="Old password wrong", status_code=status.HTTP_400_BAD_REQUEST)
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            return standard_response(success=True, message="Changed.")
        return standard_response(success=False, errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

class AccountDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = AccountDeleteSerializer
    def delete(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            if not request.user.check_password(serializer.validated_data['password']):
                return standard_response(success=False, message="Wrong password", status_code=status.HTTP_400_BAD_REQUEST)
            send_account_deletion_email(request.user)
            request.user.delete()
            return standard_response(success=True, message="Deleted.")
        return standard_response(success=False, errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try: return standard_response(success=True, data=super().post(request, *args, **kwargs).data)
        except Exception as e: return standard_response(success=False, message=str(e), status_code=status.HTTP_401_UNAUTHORIZED)

class CustomTokenVerifyView(TokenVerifyView):
    def post(self, request, *args, **kwargs):
        try: return standard_response(success=True, data={'valid': True})
        except Exception as e: return standard_response(success=False, message=str(e), status_code=status.HTTP_401_UNAUTHORIZED)

@csrf_exempt
def delete_profile_data_request_view(request): return render(request, 'users/delete_profile_data_request.html')

def privacy_policy_view(request):
    return render(request, 'users/privacy_policy.html')

@method_decorator(csrf_exempt, name='dispatch')
class ProfileDataDeletionAPIView(View):
    def get(self, request):
        return render(request, 'users/delete_profile_data_request.html')

    def post(self, request):
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            ProfileDataDeletionRequest.objects.get_or_create(user=user, email=email)
        return render(request, 'users/delete_profile_data_submitted.html', {'email': email})

class VerifyProfileDataDeletionView(View):
    def get(self, request, token):
        try:
            req = ProfileDataDeletionRequest.objects.get(verification_token=token, status='pending')
            user = req.user
            req.status = 'completed'
            req.save()
            if user:
                user.delete()
            return render(request, 'users/delete_profile_data_confirmed.html')
        except Exception as e:
            from django.http import HttpResponseBadRequest
            return HttpResponseBadRequest("Invalid link or request expired")

@csrf_exempt
def account_deletion_request_view(request): return render(request, 'users/delete_account.html')

@method_decorator(csrf_exempt, name='dispatch')
class AccountDeletionAPIView(View):
    def get(self, request):
        return render(request, 'users/delete_account.html')

    def post(self, request):
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            AccountDeletionRequest.objects.get_or_create(user=user, email=email)
        return render(request, 'users/deletion_request_submitted.html', {'email': email})

class VerifyAccountDeletionView(View):
    def get(self, request, token):
        try:
            req = AccountDeletionRequest.objects.get(verification_token=token, status='pending')
            user = req.user
            req.status = 'completed'
            req.save()
            if user:
                user.delete()
            return render(request, 'users/deletion_confirmed.html')
        except Exception as e:
            from django.http import HttpResponseBadRequest
            return HttpResponseBadRequest("Invalid link or request expired")

class OtherUserProfileView(APIView):
    """
    View another user's public profile by their ID.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk, is_email_verified=True)
            serializer = PublicUserProfileSerializer(user, context={'request': request})
            return standard_response(
                success=True,
                message="User profile retrieved successfully",
                data={**serializer.data, 'account_type': 'personal'}
            )
        except User.DoesNotExist:
            return standard_response(
                success=False,
                message="Account not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            token = RefreshToken(request.data.get('refresh'))
            token.blacklist()
            return standard_response(success=True, message="Logged out")
        except: return standard_response(success=True, message="Logged out")

class UserFitnessInfoUpdateView(APIView):
    """
    API view to update user fitness information after email verification.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = UserFitnessInfoSerializer

    def post(self, request):
        serializer = self.serializer_class(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            user.is_profile_complete = True
            user.save(update_fields=['is_profile_complete'])
            return standard_response(
                success=True, 
                message="Fitness information updated successfully", 
                data={**serializer.data, 'is_profile_complete': user.is_profile_complete}
            )
        return standard_response(
            success=False, 
            message="Validation failed", 
            errors=serializer.errors, 
            status_code=status.HTTP_400_BAD_REQUEST
        )
