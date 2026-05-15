from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Delete users who haven\'t verified their email within 24 hours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Age in hours after which unverified users should be deleted'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        cutoff = timezone.now() - timezone.timedelta(hours=hours)
        
        unverified_users = User.objects.filter(
            is_email_verified=False,
            date_joined__lt=cutoff
        )
        
        count = unverified_users.count()
        emails = list(unverified_users.values_list('email', flat=True))
        
        if count > 0:
            unverified_users.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} unverified users: {", ".join(emails)}'))
        else:
            self.stdout.write(self.style.SUCCESS('No unverified users found to delete.'))
