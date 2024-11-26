from django.core.management.base import BaseCommand
from django.core.management import call_command
from app_truyen.models import Story

class Command(BaseCommand):
    help = 'Get all stories and fetch missing chapters using the child command'

    def handle(self, *args, **kwargs):
        self.stdout.write("Fetching all stories from the database...")

        # Lấy tất cả các stories với title và chapter_number
        stories = Story.objects.values('title', 'chapter_number')

        if not stories:
            self.stdout.write(self.style.WARNING("No stories found in the database."))
            return
        # Neu chapter_number bang 0 thi goi get_story_info
        for story in stories:
            if story['chapter_number'] == 0:
                # self.stdout.write(f"Processing story '{story['title']}'...")
                try:
                    call_command('get_story_info', story['title'])
                    # self.stdout.write(self.style.SUCCESS(f"Successfully processed story '{story['title']}'."))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing story '{story['title']}': {e}"))
