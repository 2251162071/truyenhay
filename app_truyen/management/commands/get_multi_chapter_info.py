import os

import requests
from django.core.management.base import BaseCommand
from app_truyen.models import Story, Chapter
from truyenhay.settings import CRAWL_URL
from django.utils import timezone
from bs4 import BeautifulSoup
from app_truyen.vpn_utils import toggle_vpn, get_vpn_status


class Command(BaseCommand):
    help = "A sample command using toggle_vpn"

    def handle(self, *args, **kwargs):
        vpn_enabled = False  # Trạng thái VPN ban đầu
        self.stdout.write("Starting VPN toggle process...")

        try:
            vpn_enabled = toggle_vpn(vpn_enabled)  # Bật VPN
            self.stdout.write(f"VPN trạng thái hiện tại: {'Enabled' if vpn_enabled else 'Disabled'}")

            # Thực hiện logic tiếp theo...

            vpn_enabled = toggle_vpn(vpn_enabled)  # Tắt VPN
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Lỗi trong quá trình xử lý VPN: {str(e)}"))


class Command(BaseCommand):
    help = 'Get chapter data for a given story and chapter numbers'

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
            for chapter_number in range(start, end + 1):
                self.stdout.write(f"Processing Chapter {chapter_number}...")
                try:
                    chapter_data = self.get_chapter_data(story_name, chapter_number)
                    if chapter_data['exists']:
                        self.stdout.write(self.style.SUCCESS(f"Chapter {chapter_number} updated: {chapter_data['chapter']}"))
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
        vpn_enabled = get_vpn_status(os.getenv('VPN_NAME'))  # Giả sử trạng thái VPN ban đầu là tắt

        while True:
            try:
                response = requests.get(chapter_url, timeout=10)
                if response.status_code == 503:
                    self.stdout.write(self.style.WARNING("503 Service Unavailable - Toggling VPN..."))
                    self.stdout.write(self.style.INFO(f"VPN status: {'Enabled' if vpn_enabled else 'Disabled'}"))
                    vpn_enabled = toggle_vpn(vpn_enabled, os.getenv('VPN_NAME'))
                    continue  # Thử lại request sau khi bật/tắt VPN
                response.raise_for_status()
                break  # Nếu request thành công, thoát khỏi vòng lặp
            except requests.RequestException as e:
                raise Exception(f"Failed to fetch URL {chapter_url}: {str(e)}")

        soup = BeautifulSoup(response.text, 'html.parser')
        chapter_title = None
        chapter_content = None

        try:
            if soup.find('h2'):
                if soup.find('h2').find('a', class_='chapter-title'):
                    chapter_title = soup.find('h2').find('a', class_='chapter-title').get_text(strip=True)
            if chapter_title is None:
                chapter_title = 'Untitled Chapter'
                self.stdout.write(self.style.WARNING("Chapter title not found"))

            chapter_content_div = soup.find('div', class_='chapter-c')
            if chapter_content_div:
                chapter_content = chapter_content_div.decode_contents() if chapter_content_div else None

            if chapter_content is None:
                chapter_content = 'No content found'
                self.stdout.write(self.style.WARNING("Chapter content not found"))
        except AttributeError:
            pass  # Nếu không tìm thấy tiêu đề hoặc nội dung, trả về None

        return chapter_content, chapter_title
