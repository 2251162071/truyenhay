import requests
import os
from bs4 import BeautifulSoup
from django.utils import timezone
from app_truyen.models import Story, Chapter
from app_truyen.vpn_utils import toggle_vpn, get_vpn_status
import logging

from data_json.proxies.h import response

logger = logging.getLogger(__name__)

def get_story_by_name(story_name):
    """
    Lấy thông tin Story từ database theo tên.
    """
    try:
        return Story.objects.get(title=story_name)
    except Story.DoesNotExist:
        raise ValueError(f"Story '{story_name}' does not exist")

def fetch_chapter_content(chapter_url):
    """
    Gửi request tới URL để lấy nội dung chương.
    """
    vpn_enabled = get_vpn_status(os.getenv('VPN_NAME'))  # Giả sử trạng thái VPN ban đầu là tắt
    while True:
        try:
            response = requests.get(chapter_url, timeout=10)
            if response.status_code == 503:
                logger.warning("503 Service Unavailable - Toggling VPN...")
                logger.info(f"VPN status: {'Enabled' if vpn_enabled else 'Disabled'}")
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
        chapter_title = soup.find('h2').find('a', class_='chapter-title').get_text(strip=True)
        chapter_content_div = soup.find('div', class_='chapter-c')
        chapter_content = chapter_content_div.decode_contents() if chapter_content_div else None
    except AttributeError:
        pass  # Nếu không tìm thấy tiêu đề hoặc nội dung, trả về None

    return chapter_title, chapter_content

def save_or_update_chapter(story_id, chapter_number, title, content):
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
