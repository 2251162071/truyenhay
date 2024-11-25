import requests
from bs4 import BeautifulSoup
import logging

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

def setup_vpn():
    """
    Thiết lập VPN mới trong Network Manager.
    """
    try:
        # Thêm kết nối VPN với Network Manager
        subprocess.run([
            "nmcli", "connection", "add",
            "type", "vpn",
            "vpn-type", "l2tp",
            "con-name", os.getenv('VPN_NAME'),
            "ifname", "--",
            "connection.autoconnect", "no",
            f"vpn.data", f"gateway={os.getenv('VPN_SERVER')},user={os.getenv('VPN_USERNAME')}"
        ], check=True)

        # Cấu hình username và password
        subprocess.run([
            "nmcli", "connection", "modify", os.getenv('VPN_NAME'),
            f"vpn.secrets", f"password={os.getenv('VPN_PASSWORD')}"
        ], check=True)

        print(f"VPN {os.getenv('VPN_NAME')} thiết lập thành công!")
    except subprocess.CalledProcessError as e:
        print(f"Lỗi thiết lập VPN: {e}")

def toggle_vpn(vpn_name, action):
    """
    Bật hoặc tắt VPN.
    action: 'up' để bật, 'down' để tắt.
    """
    try:
        if action == "up":
            subprocess.run(["nmcli", "connection", "up", vpn_name], check=True)
            print(f"VPN {vpn_name} đã được bật.")
        elif action == "down":
            subprocess.run(["nmcli", "connection", "down", vpn_name], check=True)
            print(f"VPN {vpn_name} đã được tắt.")
        else:
            print("Hành động không hợp lệ. Chỉ chấp nhận 'up' hoặc 'down'.")
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi {action} VPN: {e}")