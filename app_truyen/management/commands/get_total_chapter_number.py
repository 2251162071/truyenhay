# app_truyen/management/commands/calculate_total_chapters.py

from django.core.management.base import BaseCommand
from django.db.models import Sum
from app_truyen.models import Story

class Command(BaseCommand):
    help = 'Calculate the total of the chapter_number field in the Story table'

    def handle(self, *args, **kwargs):
        total_chapters = Story.objects.aggregate(total=Sum('chapter_number'))['total']
        self.stdout.write(f"Total chapters: {total_chapters}")