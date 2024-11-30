from django.core.management.base import BaseCommand
from app_truyen.models import Story
from django.core.management import call_command
import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update missing chapters for all stories'

    def handle(self, *args, **kwargs):
        # Đọc tất cả record trong bảng story và lấy title
        stories = Story.objects.all()

        # Lặp qua tất cả các title
        for story in stories:
            self.stdout.write(f"Processing story: {story.title}")

            # Gọi command get_missing_chapters cho từng title
            try:
                if story.chapter_number > 0:
                    call_command('get_missing_chapters', story.title, '--chapter_range', '1-50'
                                                                                         '')
            except Exception as e:
                self.stderr.write(f"Error while processing story '{story.title}': {e}")
                # logger.error(f"====[{story.title}]====Error while processing: {e}")

        self.stdout.write(self.style.SUCCESS('Successfully updated all missing chapters'))
