import logging
from multiprocessing.sharedctypes import class_cache

import requests
from bs4 import BeautifulSoup
from django.utils import timezone

from app_truyen.models import Chapter

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_page_content(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.Timeout:
        logger.error(f"Request to {url} timed out.")
    except requests.RequestException as e:
        logger.error(f"Request failed for {url}: {str(e)}")
    return None

def get_chapter_content(chapter_url):
    try:
        page_content = fetch_page_content(chapter_url)
        if not page_content:
            return None, None

        soup = BeautifulSoup(page_content, 'html.parser')

        # Kiểm tra và lấy tiêu đề chương
        chapter_title_element = soup.find('h2')
        if not chapter_title_element:
            logger.error(f"Chapter title not found in {chapter_url}")
            return None, None
        chapter_title = chapter_title_element.find('a', class_='chapter-title')
        chapter_title = chapter_title.get_text(strip=True) if chapter_title else "Untitled Chapter"

        # Lấy nội dung chương
        chapter_content = soup.find('div', class_='chapter-c')
        chapter_content = chapter_content.decode_contents() if chapter_content else None

        return chapter_content, chapter_title
    except Exception as e:
        logger.error(f"Unexpected error processing {chapter_url}: {str(e)}")
        return None, None


def send_request(url):
    """
    Gửi request đến URL và trả về response.

    Args:
        url (str): URL cần gửi request.
        'https://example.com/'

    Returns:
        requests.models.Response: Response từ request.

    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Kiểm tra lỗi HTTP
        # print(Fore.GREEN + f"Gửi request thành công: {url}")
        logger.error(f"Gửi request thành công: {url}")
        return response
    except requests.RequestException as e:
        # print(Fore.RED + f"Có lỗi khi gửi request: {e}")
        logger.error(f"Có lỗi khi gửi request: {e}")
        return None


# VPN Service
import subprocess
import os

# def setup_vpn():
#     """
#     Thiết lập VPN mới trong Network Manager.
#     """
#     try:
#         # Thêm kết nối VPN với Network Manager
#         subprocess.run([
#             "nmcli", "connection", "add",
#             "type", "vpn",
#             "vpn-type", "l2tp",
#             "con-name", os.getenv('VPN_NAME'),
#             "ifname", "--",
#             "connection.autoconnect", "no",
#             f"vpn.data", f"gateway={os.getenv('VPN_SERVER')},user={os.getenv('VPN_USERNAME')}"
#         ], check=True)
#
#         # Cấu hình username và password
#         subprocess.run([
#             "nmcli", "connection", "modify", os.getenv('VPN_NAME'),
#             f"vpn.secrets", f"password={os.getenv('VPN_PASSWORD')}"
#         ], check=True)
#
#         print(f"VPN {os.getenv('VPN_NAME')} thiết lập thành công!")
#     except subprocess.CalledProcessError as e:
#         print(f"Lỗi thiết lập VPN: {e}")
#
# def toggle_vpn(vpn_name, action):
#     """
#     Bật hoặc tắt VPN.
#     action: 'up' để bật, 'down' để tắt.
#     """
#     try:
#         if action == "up":
#             subprocess.run(["nmcli", "connection", "up", vpn_name], check=True)
#             print(f"VPN {vpn_name} đã được bật.")
#         elif action == "down":
#             subprocess.run(["nmcli", "connection", "down", vpn_name], check=True)
#             print(f"VPN {vpn_name} đã được tắt.")
#         else:
#             print("Hành động không hợp lệ. Chỉ chấp nhận 'up' hoặc 'down'.")
#     except subprocess.CalledProcessError as e:
#         print(f"Lỗi khi {action} VPN: {e}")

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
        if soup.find('h2') is not None:
            if soup.find('a', class_='chapter-title') is not None:
                chapter_title = soup.find('h2').find('a', class_='chapter-title').get_text(strip=True)
        if chapter_title is None:
            chapter_title = "Untitled Chapter"
        chapter_content_div = soup.find('div', class_='chapter-c')
        chapter_content = chapter_content_div.decode_contents() if chapter_content_div else 'No content found'
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

def get_vpn_status(vpn_name):
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

def toggle_vpn(vpn_enabled, vpn_name=None):
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