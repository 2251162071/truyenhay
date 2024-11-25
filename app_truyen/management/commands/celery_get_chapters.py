from django.core.management.base import BaseCommand
from app_truyen.tasks import fetch_chapter
from truyenhay.settings import CRAWL_URL

class Command(BaseCommand):
    help = 'Get chapter data for a given story and chapter numbers'

    def add_arguments(self, parser):
        parser.add_argument('story_name', type=str, help='Name of the story')
        parser.add_argument('--chapter_range', type=str, help='Range of chapter numbers, e.g., "1-5"', required=True)

    def handle(self, *args, **kwargs):
        story_name = kwargs['story_name']
        chapter_range = kwargs['chapter_range']

        try:
            start, end = self.parse_range(chapter_range)
            tasks = []
            for chapter_number in range(start, end + 1):
                self.stdout.write(f"Queuing task for Chapter {chapter_number}...")
                task = fetch_chapter.delay(story_name, chapter_number, CRAWL_URL)
                tasks.append(task)

            # Wait for tasks to complete and report results
            for task in tasks:
                result = task.get(timeout=30)  # Wait for up to 30 seconds per task
                if result['exists']:
                    self.stdout.write(self.style.SUCCESS(f"Chapter processed: {result['chapter']}"))
                else:
                    self.stdout.write(self.style.ERROR(f"Error: {result['error']}"))
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f"Invalid chapter range: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))

    def parse_range(self, chapter_range):
        try:
            start, end = map(int, chapter_range.split('-'))
            if start > end:
                raise ValueError("Start of the range cannot be greater than the end.")
            return start, end
        except Exception:
            raise ValueError("Chapter range must be in the format 'start-end' with valid integers.")
