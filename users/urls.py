from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserLogoutView,
    VerifyOTPView,
    ResendOTPView,
    PasswordResetRequestView,
    PasswordResetOTPVerifyView,
    PasswordResetConfirmView,
    PasswordChangeView,
    UserProfileView,
    AccountDeleteView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    account_deletion_request_view,
    AccountDeletionAPIView,
    VerifyAccountDeletionView,
    delete_profile_data_request_view,
    ProfileDataDeletionAPIView,
    VerifyProfileDataDeletionView,
    SupportTicketView,
    OtherUserProfileView,
    UserFitnessInfoUpdateView,
    privacy_policy_view,
)

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('signup/', UserRegistrationView.as_view(), name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    
    # Token management
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('token/verify/', CustomTokenVerifyView.as_view(), name='token-verify'),
    
    # OTP verification
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    
    # Password management
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-otp-verify/', PasswordResetOTPVerifyView.as_view(), name='password-reset-otp-verify'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('password-change/', PasswordChangeView.as_view(), name='password-change'),
    
    # Profile management
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('account-delete/', AccountDeleteView.as_view(), name='account-delete'),
    path('support-ticket/', SupportTicketView.as_view(), name='support-ticket'),
    path('fitness-info/', UserFitnessInfoUpdateView.as_view(), name='fitness-info'),
    path('profile/<uuid:pk>/', OtherUserProfileView.as_view(), name='other-user-profile'),

    # Account Deletion
    path('delete-account/', account_deletion_request_view, name='delete-account-form'),
    path('delete-account-request/', AccountDeletionAPIView.as_view(), name='delete-account-request'),
    path('verify-account-deletion/<uuid:token>/', VerifyAccountDeletionView.as_view(), name='verify_account_deletion'),

    # Profile Data Deletion
    path('delete-profile-data/', delete_profile_data_request_view, name='delete-profile-data-form'),
    path('delete-profile-data-request/', ProfileDataDeletionAPIView.as_view(), name='delete-profile-data-request'),
    path('verify-profile-data-deletion/<uuid:token>/', VerifyProfileDataDeletionView.as_view(), name='verify_profile_data_deletion'),

    # Privacy Policy (Unauthenticated for Play Store requirements)
    path('privacy-policy/', privacy_policy_view, name='privacy-policy'),
]
