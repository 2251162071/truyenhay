import requests
from django.core.management.base import BaseCommand
from app_truyen.models import Story, Chapter
from truyenhay.settings import CRAWL_URL
from django.utils import timezone
from bs4 import BeautifulSoup


class Command(BaseCommand):
    help = 'Get missing chapters for a given story and add them to the database'

    def add_arguments(self, parser):
        parser.add_argument(
            'story_name',
            type=str,
            help='Name of the story'
        )
        parser.add_argument(
            '--chapter_range',
            type=str,
            help='Range of chapter numbers, e.g., "1-5"',
            required=True
        )

    def handle(self, *args, **kwargs):
        story_name = kwargs['story_name']
        chapter_range = kwargs['chapter_range']

        try:
            start, end = self.parse_range(chapter_range)
            try:
                story = Story.objects.get(title=story_name)
            except Story.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Story '{story_name}' does not exist"))
                return

            existing_chapters = Chapter.objects.filter(story=story, chapter_number__range=(start, end)).values_list('chapter_number', flat=True)
            missing_chapters = set(range(start, end + 1)) - set(existing_chapters)

            if not missing_chapters:
                self.stdout.write(self.style.SUCCESS(f"All chapters from {start} to {end} already exist in the database."))
                return

            self.stdout.write(f"Missing chapters: {', '.join(map(str, sorted(missing_chapters)))}")

            for chapter_number in sorted(missing_chapters):
                self.stdout.write(f"Processing missing Chapter {chapter_number}...")
                try:
                    chapter_data = self.get_chapter_data(story_name, chapter_number, story.id)
                    if chapter_data['exists']:
                        self.stdout.write(self.style.SUCCESS(f"Chapter {chapter_number} added: {chapter_data['chapter']}"))
                    else:
                        self.stdout.write(self.style.ERROR(f"Error: {chapter_data['error']}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error with Chapter {chapter_number}: {str(e)}"))
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f"Invalid chapter range: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))

    def parse_range(self, chapter_range):
        """
        Parse the range string into start and end numbers.
        Args:
            chapter_range (str): A string in the format "start-end".

        Returns:
            tuple: A tuple of (start, end).

        Raises:
            ValueError: If the range format is invalid.
        """
        try:
            start, end = map(int, chapter_range.split('-'))
            if start > end:
                raise ValueError("Start of the range cannot be greater than the end.")
            return start, end
        except Exception:
            raise ValueError("Chapter range must be in the format 'start-end' with valid integers.")

    def get_chapter_data(self, story_name, chapter_number, story_id):
        chapter_url = f"{CRAWL_URL}/{story_name}/chuong-{chapter_number}"
        chapter_content, chapter_title = self.get_chapter_content(chapter_url)

        if not chapter_content:
            return {'exists': False, 'error': 'Failed to fetch chapter content'}

        # Tạo mới Chapter
        chapter, created = Chapter.objects.get_or_create(
            story_id=story_id,
            chapter_number=chapter_number,
            defaults={
                'title': chapter_title,
                'content': chapter_content,
                'views': 0,
                'updated_at': timezone.now()
            }
        )
        return {'exists': True, 'chapter': f"{chapter.title} (Chapter {chapter_number})"}

    def get_chapter_content(self, chapter_url):
        try:
            response = requests.get(chapter_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch URL {chapter_url}: {str(e)}")

        soup = BeautifulSoup(response.text, 'html.parser')
        chapter_title = None
        chapter_content = None

        try:
            chapter_title = soup.find('h2').find('a', class_='chapter-title').get_text(strip=True)
            chapter_content_div = soup.find('div', class_='chapter-c')
            chapter_content = chapter_content_div.decode_contents() if chapter_content_div else None
        except AttributeError:
            pass  # Nếu không tìm thấy tiêu đề hoặc nội dung, trả về None

        return chapter_content, chapter_title
