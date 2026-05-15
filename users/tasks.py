from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

@shared_task
def send_otp_email_task(user_email, otp):
    """
    Celery task to send OTP to user's email
    """
    try:
        subject = 'Your One-Time Password (OTP)'
        html_message = render_to_string('emails/otp_email.html', {
            'otp': otp,
            'site_name': 'Your App Name',
        })
        plain_message = strip_tags(html_message)
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        return "OTP email sent successfully."
    except Exception as e:
        return f"Error sending OTP email: {str(e)}"

@shared_task
def delete_unverified_users_task():
    """
    Periodic task to delete users who haven't verified their email within 24 hours.
    """
    cutoff = timezone.now() - timezone.timedelta(hours=24)
    unverified_users = User.objects.filter(
        is_email_verified=False,
        date_joined__lt=cutoff
    )
    count = unverified_users.count()
    unverified_users.delete()
    return f"Deleted {count} unverified users."