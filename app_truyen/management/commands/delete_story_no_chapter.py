from django.core.management.base import BaseCommand
from app_truyen.models import Story

class Command(BaseCommand):
    help = 'Delete stories with chapter_number equal to 0'

    def handle(self, *args, **kwargs):
        deleted_count, _ = Story.objects.filter(chapter_number=0).delete()
        self.stdout.write(f"Deleted {deleted_count} stories with chapter_number equal to 0.")