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

        # Lặp qua từng story và gọi child command
        for story in stories:
            title = story['title']
            if not isinstance(story['chapter_number'], int):
                chapter_number = 1
            else:
                chapter_number = int(story['chapter_number'])

            if chapter_number == 0:
                continue
            chapter_range = f"1-{chapter_number}"

            self.stdout.write(self.style.SUCCESS(f"Processing story '{title}' with chapter range '{chapter_range}'..."))

            try:
                # Gọi child command
                call_command('get_missing_chapters', title, '--chapter_range', chapter_range)
                self.stdout.write(self.style.SUCCESS(f"Successfully processed story '{title}'."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing story '{title}': {e}"))
