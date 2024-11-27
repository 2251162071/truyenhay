import requests
from django.core.management.base import BaseCommand
from app_truyen.models import Story, Chapter
from truyenhay.settings import CRAWL_URL
from django.utils import timezone
from bs4 import BeautifulSoup
import subprocess
import logging
import os
import re

logger = logging.getLogger(__name__)


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

            # self.stdout.write(f"Missing chapters: {', '.join(map(str, sorted(missing_chapters)))}")

            for chapter_number in sorted(missing_chapters):
                # self.stdout.write(f"Processing missing Chapter {chapter_number}...")
                try:
                    chapter_data = self.get_chapter_data(story_name, chapter_number, story.id)
                    # if chapter_data['exists']:
                    #     self.stdout.write(self.style.SUCCESS(f"Chapter {chapter_number} added: {chapter_data['chapter']}"))
                    # else:
                    #     self.stdout.write(self.style.ERROR(f"Error: {chapter_data['error']}"))
                    if not chapter_data['exists']:
                        self.stdout.write(self.style.ERROR(f"Error with Chapter {chapter_number}: {chapter_data['error']}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error with Chapter {chapter_number}: {str(e)}"))
                    break  # Nếu có lỗi, thoát khỏi vòng lặp
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f"Invalid chapter range: {str(e)} chapter_range: {chapter_range}"))
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
        if requests.get(chapter_url).status_code == 404:
            return {'exists': False, 'error': f"Chapter {chapter_number} from {story_name} not found"}
        chapter_title, chapter_content = self.fetch_chapter_content(chapter_url)

        if not chapter_content:
            return {'exists': False, 'error': f'Failed to fetch chapter content {chapter_url}'}

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

    def get_story_by_name(self, story_name):
        """
        Lấy thông tin Story từ database theo tên.
        """
        try:
            return Story.objects.get(title=story_name)
        except Story.DoesNotExist:
            raise ValueError(f"Story '{story_name}' does not exist")

    def fetch_chapter_content(self, chapter_url):
        """
        Gửi request tới URL để lấy nội dung chương.
        """
        vpn_enabled = self.get_vpn_status(os.getenv('VPN_NAME'))  # Giả sử trạng thái VPN ban đầu là tắt
        while True:
            try:
                response = requests.get(chapter_url, timeout=10)
                if response.status_code == 503:
                    logger.warning("503 Service Unavailable - Toggling VPN...")
                    logger.info(f"VPN status: {'Enabled' if vpn_enabled else 'Disabled'}")
                    vpn_enabled = self.toggle_vpn(vpn_enabled, os.getenv('VPN_NAME'))
                    continue  # Thử lại request sau khi bật/tắt VPN
                response.raise_for_status()
                break  # Nếu request thành công, thoát khỏi vòng lặp
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

        return chapter_title, chapter_content

    def save_or_update_chapter(self, story_id, chapter_number, title, content):
        """
        Lưu hoặc cập nhật chapter trong database.
        """
        chapter, created = Chapter.objects.get_or_create(
            story_id=story_id,
            chapter_number=chapter_number,
            defaults={
                'title': title,
                'content': content,
                'views': 0,
                'updated_at': timezone.now()
            }
        )
        if not created:  # Nếu chapter đã tồn tại, cập nhật thông tin
            chapter.title = title
            chapter.content = content
            chapter.updated_at = timezone.now()
            chapter.save()

        return chapter, created

    def get_vpn_status(self, vpn_name):
        """
        Kiểm tra trạng thái của VPN.
        Args:
            vpn_name (str): Tên của VPN cần kiểm tra.

        Returns:
            bool: True nếu VPN đang được bật, False nếu VPN đang tắt.
        """
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "NAME,TYPE,STATE", "connection", "show", "--active"],
                stdout=subprocess.PIPE,
                text=True,
                check=True
            )
            # Kiểm tra nếu VPN đang hoạt động
            active_connections = result.stdout.strip().split('\n')
            for connection in active_connections:
                name, conn_type, state = connection.split(':')
                if name == vpn_name and conn_type == "vpn" and state == "activated":
                    logger.info(f"VPN {vpn_name} đang được bật.")
                    return True
            logger.info(f"VPN {vpn_name} đang tắt.")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Lỗi khi kiểm tra trạng thái VPN: {e}")
            raise

    def toggle_vpn(self, vpn_enabled, vpn_name=None):
        """
        Bật hoặc tắt VPN.
        Args:
            vpn_enabled (bool): Trạng thái hiện tại của VPN.
            vpn_name (str, optional): Tên VPN. Mặc định lấy từ biến môi trường VPN_NAME.

        Returns:
            bool: Trạng thái VPN sau khi thay đổi.
        """
        vpn_name = vpn_name or os.getenv('VPN_NAME')
        if not vpn_name:
            raise ValueError("VPN_NAME environment variable is not set.")

        try:
            # current_status = get_vpn_status(vpn_name)
            # if vpn_enabled == current_status:
            #     logger.info(f"VPN {vpn_name} đã ở trạng thái mong muốn ({'Enabled' if vpn_enabled else 'Disabled'}).")
            #     return vpn_enabled

            if not vpn_enabled:
                logger.info("Enabling VPN...")
                subprocess.run(["nmcli", "connection", "up", vpn_name], check=True)
                logger.info(f"VPN {vpn_name} đã được bật.")
            else:
                logger.info("Disabling VPN...")
                subprocess.run(["nmcli", "connection", "down", vpn_name], check=True)
                logger.info(f"VPN {vpn_name} đã được tắt.")
            return not vpn_enabled
        except subprocess.CalledProcessError as e:
            logger.error(f"Lỗi khi bật/tắt VPN: {e}")
            raise
