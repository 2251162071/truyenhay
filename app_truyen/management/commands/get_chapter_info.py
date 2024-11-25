import requests
from django.core.management.base import BaseCommand
from app_truyen.models import Story, Chapter
from truyenhay.settings import CRAWL_URL
from django.utils import timezone
from bs4 import BeautifulSoup


class Command(BaseCommand):
    help = 'Get chapter data for a given story and chapter number'

    def add_arguments(self, parser):
        parser.add_argument(
            'story_name',
            type=str,
            help='Name of the story'
        )
        parser.add_argument(
            'chapter_number',
            type=int,
            help='Number of the chapter'
        )

    def handle(self, *args, **kwargs):
        story_name = kwargs['story_name']
        chapter_number = kwargs['chapter_number']
        try:
            chapter_data = self.get_chapter_data(story_name, chapter_number)
            if chapter_data['exists']:
                self.stdout.write(self.style.SUCCESS(f"Chapter data updated: {chapter_data['chapter']}"))
            else:
                self.stdout.write(self.style.ERROR(f"Error: {chapter_data['error']}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))

    def get_chapter_data(self, story_name, chapter_number):
        try:
            # Tìm kiếm Story
            story = Story.objects.get(title=story_name)
        except Story.DoesNotExist:
            return {'exists': False, 'error': f"Story '{story_name}' does not exist"}

        # Lấy nội dung chapter từ URL
        chapter_url = f"{CRAWL_URL}/{story_name}/chuong-{chapter_number}"
        chapter_content, chapter_title = self.get_chapter_content(chapter_url)

        if not chapter_content:
            return {'exists': False, 'error': 'Failed to fetch chapter content'}

        # Cập nhật hoặc tạo mới Chapter
        chapter, created = Chapter.objects.get_or_create(
            story_id=story.id,
            chapter_number=chapter_number,
            defaults={
                'title': chapter_title,
                'content': chapter_content,
                'views': 0,
                'updated_at': timezone.now()
            }
        )
        if not created:  # Nếu Chapter đã tồn tại, chỉ cập nhật các trường cần thiết
            chapter.title = chapter_title
            chapter.content = chapter_content
            chapter.updated_at = timezone.now()
            chapter.save()

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
