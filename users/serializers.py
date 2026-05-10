"""
API Serializers for user authentication and profile management
All serializers follow standard response format for consistency
"""

from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .validators import (
    validate_password_strength,
    validate_email_format,
    validate_name,
    validate_date_of_birth,
    validate_password_match,
    validate_profile_picture
)
from .exceptions import (
    InvalidCredentialsException,
    EmailNotVerifiedException,
    PasswordMismatchException,
    EmailAlreadyExistsException,
)
from .utils import validate_age

from .models import UserLoginHistory, AccountDeletionRequest, ProfileDataDeletionRequest

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration (signup)
    """
    
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Password confirmation"
    )
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="User's password (min 8 chars, must include uppercase, lowercase, number, special char)"
    )
    
    class Meta:
        model = User
        fields = ['email', 'password', 'confirm_password', 'full_name']
    
    def validate_email(self, value):
        """Validate email format and check if it already exists"""
        try:
            validate_email_format(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        
        return value.lower()
    
    def validate_password(self, value):
        """Validate password strength"""
        try:
            validate_password_strength(value)
            django_validate_password(value)
            return value
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
    
    def validate(self, attrs):
        """Validate that passwords match"""
        try:
            validate_password_match(attrs['password'], attrs['confirm_password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({'confirm_password': str(e)})
        
        return attrs
    
    def create(self, validated_data):
        """Create new user and send OTP"""
        validated_data.pop('confirm_password')
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        user = User.objects.create_user(email, password, **validated_data)
        user.is_active = False
        
        from .utils import generate_otp, send_otp_email
        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save(update_fields=['otp', 'otp_created_at', 'is_active'])
        send_otp_email(user, otp)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    
    email = serializers.EmailField(
        required=True,
        help_text="User's email address"
    )
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="User's password"
    )
    
    def validate(self, attrs):
        """Validate user credentials"""
        email = attrs.get('email', '').lower()
        password = attrs.get('password')
        
        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise InvalidCredentialsException("Invalid email or password")
            
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
            
            user = authenticate(email=email, password=password)
            
            if not user:
                raise InvalidCredentialsException("Invalid email or password")
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'.")


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification
    """
    token = serializers.CharField(
        required=True,
        help_text="Email verification token sent to user's email"
    )


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting password reset
    """
    email = serializers.EmailField(
        required=True,
        help_text="Email address of the account to reset password"
    )
    
    def validate_email(self, value):
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset with OTP
    """
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="New password"
    )
    
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Password confirmation"
    )
    
    def validate_password(self, value):
        try:
            validate_password_strength(value)
            django_validate_password(value)
            return value
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
    
    def validate(self, attrs):
        try:
            validate_password_match(attrs['password'], attrs['confirm_password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({'confirm_password': str(e)})
        
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing password (authenticated user)
    """
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Current password"
    )
    
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="New password"
    )
    
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="New password confirmation"
    )
    
    def validate_new_password(self, value):
        try:
            validate_password_strength(value)
            django_validate_password(value)
            return value
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
    
    def validate(self, attrs):
        try:
            validate_password_match(attrs['new_password'], attrs['confirm_password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({'confirm_password': str(e)})
        
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                'new_password': 'New password must be different from old password.'
            })
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile (read and update)
    """
    
    author_id = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField(
        read_only=True,
        help_text="User's age calculated from date of birth"
    )

    class Meta:
        model = User
        fields = [
            'id',
            'author_id',
            'email',
            'full_name',
            'date_of_birth',
            'gender',
            'age',
            'profile_picture',
            'cover_photo',
            'is_email_verified',
            'date_joined',
            'last_login',
        ]
        read_only_fields = [
            'id',
            'author_id',
            'email',
            'is_email_verified',
            'date_joined',
            'last_login',
        ]

    def get_author_id(self, obj):
        return str(obj.id)
    
    def get_age(self, obj):
        """Calculate age from date of birth"""
        from .utils import calculate_age
        return calculate_age(obj.date_of_birth)

    def to_representation(self, instance):
        """Ensure absolute URLs for profile_picture and cover_photo"""
        representation = super().to_representation(instance)
        request = self.context.get('request')
        
        if request:
            if instance.profile_picture:
                representation['profile_picture'] = request.build_absolute_uri(instance.profile_picture.url)
            if instance.cover_photo:
                representation['cover_photo'] = request.build_absolute_uri(instance.cover_photo.url)
        
        return representation

    def validate_full_name(self, value):
        try:
            validate_name(value)
            return value
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_date_of_birth(self, value):
        try:
            validate_date_of_birth(value)
            if not validate_age(value, min_age=13):
                raise serializers.ValidationError("You must be at least 13 years old.")
            return value
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_profile_picture(self, value):
        if value:
            try:
                validate_profile_picture(value)
                return value
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e))
        return value


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile
    """
    class Meta:
        model = User
        fields = ['full_name', 'date_of_birth', 'gender', 'profile_picture', 'cover_photo']
    
    def validate_full_name(self, value):
        try:
            validate_name(value)
            return value
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_date_of_birth(self, value):
        try:
            validate_date_of_birth(value)
            if not validate_age(value, min_age=13):
                raise serializers.ValidationError("You must be at least 13 years old.")
            return value
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_profile_picture(self, value):
        if value:
            try:
                validate_profile_picture(value)
                return value
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e))
        return value


class AccountDeleteSerializer(serializers.Serializer):
    """
    Serializer for account deletion confirmation
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Enter your password to confirm account deletion"
    )
    
    confirm_deletion = serializers.BooleanField(
        required=True,
        help_text="Must be set to true to confirm deletion"
    )
    
    def validate_confirm_deletion(self, value):
        if not value:
            raise serializers.ValidationError("You must confirm that you want to delete your account.")
        return value


class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField(help_text="New access token")
    refresh = serializers.CharField(help_text="New refresh token (if rotation enabled)")


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)

class PasswordResetOTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

class TokenVerifyResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField(help_text="Whether token is valid")
    user_id = serializers.UUIDField(help_text="User ID from token", required=False)


class UserFitnessInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['age', 'gender', 'goal', 'height', 'height_unit', 'current_weight', 'goal_weight']


class SupportTicketSerializer(serializers.Serializer):
    email_address = serializers.EmailField(help_text="User's email address for contact")
    subject = serializers.CharField(max_length=255, help_text="Subject of the support request")
    message = serializers.CharField(style={'base_template': 'textarea.html'}, help_text="Detailed support message")


class PublicUserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing another user's public profile
    """
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 
            'profile_picture', 'cover_photo'
        ]
