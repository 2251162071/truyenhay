import os
import re

import requests
from django.core.management.base import BaseCommand

from app_truyen import utils
from app_truyen.models import Story, Chapter
from truyenhay.settings import CRAWL_URL
from django.utils import timezone
from bs4 import BeautifulSoup
import subprocess
import logging

logger = logging.getLogger(__name__)

"""
Command to get chapter data for a given story and chapter number.
python manage.py get_chapter_info <story_name> <chapter_number>
"""
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
            story = self.get_story_by_name(story_name)
            chapter_url = f"{CRAWL_URL}/{story_name}/chuong-{chapter_number}"
            # import pdb
            # pdb.set_trace()
            print('chapter_url', chapter_url)
            title, content = self.fetch_chapter_content(chapter_url)
            if title is None:
                self.stdout.write(self.style.ERROR(f"====[{story_name}]====Chapter {chapter_number} not found"))
                return
            chapter, created = self.save_or_update_chapter(story.id, chapter_number, title, content)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Chapter {chapter_number} added: {chapter.title}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Chapter {chapter_number} updated: {chapter.title}"))
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))

    def get_story_by_name(self, story_name):
        """
        Lấy thông tin Story từ database theo tên.
        """
        print(f"Looking for story: {story_name}")

        try:
            return Story.objects.get(title=story_name)
        except Story.DoesNotExist:
            raise ValueError(f"Story '{story_name}' does not exist")

    def fetch_chapter_content(self, chapter_url):
        """
        Gửi request tới URL để lấy nội dung chương.
        """
        response = utils.send_request(chapter_url)
        # import pdb
        # pdb.set_trace()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Tìm text TRUYỆN CÙNG TÁC GIẢ trong soup
        result = soup.find_all('div', class_='book-intro')

        if result:
            return None, None

        chapter_title = None
        chapter_content = None

        try:
            chapter_title = soup.find('h2').find('a', class_='chapter-title').get_text(strip=True)
            chapter_content_div = soup.find('div', class_='chapter-c')
            chapter_content = chapter_content_div.decode_contents() if chapter_content_div else None
        except AttributeError:
            pass  # Nếu không tìm thấy tiêu đề hoặc nội dung, trả về None

        return chapter_title, chapter_content

    def save_or_update_chapter(self, story_id, chapter_number, title, content):
        """
        Lưu hoặc cập nhật chapter trong database.
        """
        chapter, created = Chapter.objects.update_or_create(
            story_id=story_id,
            chapter_number=chapter_number,
            defaults={
                'content': content,
                'views': 0,
                'updated_at': timezone.now()
            }
        )
        if not created:  # Nếu chapter đã tồn tại, cập nhật thông tin
            chapter.content = content
            chapter.updated_at = timezone.now()
            chapter.save()

        return chapter, created

    def change_title(self, title):
        pattern = r"(Chương)(\d+)(.*)"
        match = re.search(pattern, title)
        if match:
            return match.group(1) + " " + match.group(2) + match.group(3)
        return title