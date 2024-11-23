from django.core.management.base import BaseCommand
from app_truyen.models import Story

class Command(BaseCommand):
    help = 'Đếm số dòng trong bảng Story'

    def handle(self, *args, **kwargs):
        count = Story.objects.count()
        self.stdout.write(f"Số dòng trong bảng MyTable: {count}")
