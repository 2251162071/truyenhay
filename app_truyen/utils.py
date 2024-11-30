import logging
import os
import re
import subprocess
import time

import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from dotenv import load_dotenv

from app_truyen.models import Chapter, Story, Genre, StoryGenre

load_dotenv()
logger = logging.getLogger(__name__)

CRAWL_URL = os.getenv('CRAWL_URL')


# Chapter
## Crawl Chapter
def crawl_chapter(story_name, chapter_number, crawl_url):
    """
    Crawl chapter content from the given URL and save it to the database.
    :param story_name: tien-nghich
    :param chapter_number: 1
    :param crawl_url: https://truyenfull.io
    :return:
    """
    # Lay story_id
    try:
        story = Story.objects.get(title=story_name)
    except Story.DoesNotExist:
        return {'exists': False, 'error': f"Story '{story_name}' does not exist"}
    # Gửi request để lấy nội dung chương
    chapter_title, chapter_content = fetch_chapter_content(f"{crawl_url}/{story_name}/chuong-{chapter_number}")

    if not chapter_title or not chapter_content:
        return {'exists': False, 'error': f"Failed to fetch chapter content for chapter {chapter_number}"}

    chapter = {
        'chapter_number': chapter_number,
        'story_id': story.id,
        'title': chapter_title,
        'content': chapter_content,
        'views': 0,
        'updated_at': timezone.now()
    }

    return {'exists': True, 'chapter': chapter}


def fetch_chapter_content(chapter_url):
    """
    Gửi request tới URL để lấy nội dung chương.
    :param chapter_url: URL của chương cần fetch
    :return: Tiêu đề chương và nội dung chương (tuple)
    """
    try:
        # Gửi request và parse nội dung HTML
        chapter_content_response = send_request(chapter_url)
        if not chapter_content_response:
            return "Invalid Chapter", "Failed to fetch chapter content"

        soup = BeautifulSoup(chapter_content_response.text, 'html.parser')

        # Tìm tiêu đề chương
        chapter_title_tag = soup.find('h2')
        chapter_title = (
            chapter_title_tag.find('a', class_='chapter-title').get_text(strip=True)
            if chapter_title_tag and chapter_title_tag.find('a', class_='chapter-title')
            else None
        )

        # Tìm nội dung chương
        chapter_content_div = soup.find('div', class_='chapter-c')
        chapter_content = (
            chapter_content_div.decode_contents()
            if chapter_content_div
            else "No content found"
        )

        return chapter_title, chapter_content

    except Exception as e:
        # Xử lý lỗi trong quá trình xử lý HTML hoặc gửi request
        print(f"Error fetching chapter content: {e}")
        return "Invalid Chapter", "Error occurred while processing content"


## Save Chapter
def save_or_update_chapter(chapter):
    chapter, created = Chapter.objects.update_or_create(
        story_id=chapter['story_id'],
        chapter_number=chapter['chapter_number'],
        defaults={
            'title': chapter['title'],
            'content': chapter['content'],
            'views': chapter['views'],
            'updated_at': chapter['updated_at']
        }
    )

    if created:
        print(f"Successfully saved chapter: {chapter.title}")
    else:
        print(f"Successfully updated chapter: {chapter.title}")
    return chapter, created


# Story
## Crawl Story
def crawl_story(story_url):
    """
    Crawl story information from the given URL and return story data.
    """
    # Gửi request và kiểm tra kết quả
    story_info_response = send_request(story_url)
    if not story_info_response:
        return {'exists': False, 'error': f"Failed to fetch story information from {story_url}"}

    soup = BeautifulSoup(story_info_response.text, 'html.parser')

    try:
        story_info = {
            "title": story_url.split('/')[-1],
            "title_full": extract_text(soup, 'h3', 'title'),
            "author": extract_text(soup, 'a', attrs={'itemprop': 'author'}),
            "genre": extract_text(soup, 'a', attrs={'itemprop': 'genre'}),
            "status": get_status(soup),
            "chapter_number": calculate_total_chapters(soup, story_url.split('/')[-1]),
            "description": get_description(soup),
            "rating": get_rating(soup),
            "views": 0,
            "updated_at": timezone.now(),
            "image": 'default.webp',
        }
        return {'exists': True, 'story_info': story_info}
    except Exception as e:
        print(f"Error processing story data from {story_url}: {e}")
        return {'exists': False, 'error': f"Error processing story data from {story_url}: {e}"}


def calculate_total_chapters(soup, story_name):
    """
    Tính tổng số chương của một truyện từ nội dung HTML đã parse.
    :param soup: Đối tượng BeautifulSoup chứa nội dung HTML của trang truyện.
    :param story_name: Tên của truyện (phần cuối của URL).
    :return: Tổng số chương (int).
    """
    try:
        # Tìm phần tử phân trang
        pagination = soup.find('ul', class_='pagination')

        # Xác định link trang cuối cùng
        if pagination:
            last_page_link = next(
                (a['href'] for a in pagination.find_all('a') if 'Cu' in a.get_text()),
                None
            )

            # Nếu không có "Cuối", tìm link trang có số lớn nhất
            if not last_page_link:
                digit_links = [
                    (a['href'], int(a.get_text()))
                    for a in pagination.find_all('a')
                    if a.get_text().isdigit()
                ]
                last_page_link = max(digit_links, key=lambda x: x[1], default=(None,))[0]
        else:
            # Nếu không có phân trang, giả định chỉ có một trang
            last_page_link = f'{CRAWL_URL}/{story_name}/trang-1/#list-chapter'

        # Gửi request đến trang cuối cùng và phân tích HTML
        last_page_link_response = send_request(last_page_link)
        last_page_link_response.raise_for_status()
        last_page_soup = BeautifulSoup(last_page_link_response.text, 'html.parser')

        # Tìm tất cả các chương trên trang cuối
        pattern = rf'{CRAWL_URL}/{story_name}/chuong-(\d+)'
        chapters = [
            int(match.group(1))
            for link in last_page_soup.find_all('a', href=True)
            if (match := re.search(pattern, link['href']))
        ]

        # Trả về số chương lớn nhất
        return max(chapters, default=0)

    except requests.RequestException as e:
        print(f"Request error: {e}")
        return 0
    except Exception as e:
        print(f"Error calculating total chapters: {e}")
        return 0


def extract_text(soup, tag, class_name=None, attrs=None, default="Unknown"):
    """
    Trích xuất văn bản từ một thẻ HTML dựa trên tag, class hoặc attributes.
    """
    element = soup.find(tag, class_=class_name, attrs=attrs)
    return element.get_text(strip=True) if element else default


def get_status(soup):
    """
    Trích xuất trạng thái của truyện từ các class cụ thể.
    """
    status_classes = ['text-primary', 'text-success', 'label-hot']
    for status_class in status_classes:
        status_tag = soup.find('span', class_=status_class)
        if status_tag:
            return status_tag.get_text(strip=True)
    return 'Unknown'


def get_description(soup):
    desc_tag = soup.find('div', class_='desc-text desc-text-full') or soup.find('div', {'itemprop': 'description'})
    return desc_tag.prettify() if desc_tag else 'Unknown'


def get_rating(soup):
    rating_tag = soup.find('span', itemprop='ratingValue')
    return float(rating_tag.get_text(strip=True)) if rating_tag else 0.0


## Save Story
def save_or_update_story(story_info):
    story, created = Story.objects.update_or_create(
        title=story_info['title'],
        defaults={
            'title_full': story_info['title_full'],
            'author': story_info['author'],
            'status': story_info['status'],
            'description': story_info['description'],
            'rating': story_info['rating'],
            'chapter_number': story_info['chapter_number'],
            'image': story_info['image'],
            'views': story_info['views'],
            'updated_at': story_info['updated_at']
        }
    )
    if created:
        print(f"Successfully saved story: {story_info['title_full']}")
    else:
        print(f"Successfully updated story: {story_info['title_full']}")

    genre = Genre.objects.filter(name_full=story_info['genre']).first()
    if genre:
        StoryGenre.objects.get_or_create(story_id=story.id, genre_id=genre.id)
    return story, created


# Genre
## Crawl Genre

## Save Genre


# HotStory

# StoryGenre

# NewUpdatedStory


# VPN
import os
import subprocess
import platform

def get_vpn_status(vpn_name):
    """
    Kiểm tra trạng thái của VPN.
    Args:
        vpn_name (str): Tên của VPN cần kiểm tra.

    Returns:
        bool: True nếu VPN đang được bật, False nếu VPN đang tắt.
    """
    try:
        if platform.system() == "Linux":
            # Kiểm tra trên Ubuntu (Linux)
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
                    print(f"VPN {vpn_name} đang được bật.")
                    return True
            print(f"VPN {vpn_name} đang tắt.")
            return False

        elif platform.system() == "Windows":
            # Kiểm tra trên Windows
            result = subprocess.run(
                ["powershell", "-Command",
                 f"Get-VpnConnection | Where-Object {{$_.Name -eq '{vpn_name}'}} | Select-Object -ExpandProperty ConnectionStatus"],
                stdout=subprocess.PIPE,
                text=True,
                check=True
            )
            connection_status = result.stdout.strip()
            if connection_status.lower() == "connected":
                print(f"VPN {vpn_name} đang được bật.")
                return True
            print(f"VPN {vpn_name} đang tắt.")
            return False

        else:
            raise NotImplementedError("Hệ điều hành không được hỗ trợ.")
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi kiểm tra trạng thái VPN: {e}")
        raise

def is_vpn_enable():
    return get_vpn_status(os.getenv('VPN_NAME'))

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
        if platform.system() == "Linux":
            if not vpn_enabled:
                print("Enabling VPN...")
                subprocess.run(["nmcli", "connection", "up", vpn_name], check=True)
                print(f"VPN {vpn_name} đã được bật.")
            else:
                print("Disabling VPN...")
                subprocess.run(["nmcli", "connection", "down", vpn_name], check=True)
                print(f"VPN {vpn_name} đã được tắt.")
        elif platform.system() == "Windows":
            if not vpn_enabled:
                print("Enabling VPN...")
                subprocess.run(["powershell", "-Command",
                                f"rasdial {vpn_name}", os.getenv('VPN_USER'), os.getenv('VPN_PASSWORD')], check=True)
                print(f"VPN {vpn_name} đã được bật.")
            else:
                print("Disabling VPN...")
                subprocess.run(["powershell", "-Command",
                                f"rasdial {vpn_name} /disconnect"], check=True)
                print(f"VPN {vpn_name} đã được tắt.")
        else:
            raise NotImplementedError("Hệ điều hành không được hỗ trợ.")
        return not vpn_enabled
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi bật/tắt VPN: {e}")
        raise



def send_request(url):
    """
    Gửi request đến URL và trả về response.
    :param url: Địa chỉ URL cần gửi request
    :return: response object hoặc thông báo lỗi
    """
    while True:
        try:
            send_response = requests.get(url, timeout=10)
            if send_response.status_code == 503:
                print("503 Service Unavailable - Toggling VPN...")
                time.sleep(5)
                toggle_vpn(is_vpn_enable(), os.getenv('VPN_NAME'))
                continue  # Thử lại sau khi bật/tắt VPN
            # Kiểm tra trạng thái HTTP, ném lỗi nếu cần
            send_response.raise_for_status()
            return send_response  # Trả về response nếu thành công
        except requests.RequestException as e:
            # Trường hợp xảy ra lỗi, in ra lỗi chi tiết
            print(f"[send_request]Failed to fetch URL {url}: {str(e)}")
            return None
