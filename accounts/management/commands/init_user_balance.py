from django.core.management.base import BaseCommand
from accounts.models import Profile

class Command(BaseCommand):
    help = '기존 사용자들에게 초기 잔액을 지급합니다'

    def handle(self, *args, **kwargs):
        profiles = Profile.objects.filter(balance__isnull=True)
        updated_count = profiles.update(balance=10000)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully initialised balance for {updated_count} users'
            )
        )