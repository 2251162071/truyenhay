import asyncio
import aiohttp
import os
import time

from bs4 import BeautifulSoup
import requests

from .models import Story, Chapter
from dotenv import load_dotenv
from asgiref.sync import sync_to_async
from .utils import fetch_chapter_content, get_vpn_status, toggle_vpn

import logging
logger = logging.getLogger(__name__)
from truyenhay.settings import CRAWL_URL

load_dotenv()

async def fetch_content(url):
    retries = 5
    delay = 5
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Referer": CRAWL_URL,  # Thay thế bằng URL bạn muốn
    }
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        soup = BeautifulSoup(await response.text(), 'html.parser')
                        chapter_content = soup.find('div', class_='chapter-c')
                        print(chapter_content)
                        return chapter_content.get_text(separator='\n', strip=True) if chapter_content else None
                    elif response.status == 503:
                        print(f"HTTP 503: Service Unavailable. Attempt {attempt + 1} of {retries}")
                        if attempt < retries - 1:
                            time.sleep(delay)  # Chờ trước khi thử lại
                        else:
                            return None
                    else:
                        logger.error(f"Lỗi HTTP {response.status} khi tải chương {url}")
                        return None
        except aiohttp.ClientError as e:
            logger.error(f"Lỗi khi tải chương {url}: {e}")
            return None

async def crawl_chapters_async(story_title, start_chapter, end_chapter):
    try:
        # Lấy thông tin truyện
        story = await sync_to_async(Story.objects.get)(title=story_title)
    except Story.DoesNotExist:
        logger.error(f"Truyện '{story_title}' không tồn tại.")
        print(f"Truyện '{story_title}' không tồn tại.")
        return
    except Exception as e:
        logger.error(f"Lỗi khi truy vấn Story: {e}")
        print(f'Lỗi khi truy vấn Story: {e}')
        return

    for chapter_number in range(start_chapter, end_chapter + 1):
        chapter_url = f"{CRAWL_URL}/{story_title}/chuong-{chapter_number}"
        fetch_chapter_content(chapter_url)



async def download_noi_dung_chuong(link_chuong):
    """
    Lấy nội dung chương từ link chương.

    Args:
        link_chuong (str): Link chương cần lấy nội dung.

    Returns:
        str: Nội dung chương.

    """

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(link_chuong) as response:
                if response.status == 200:
                    soup = BeautifulSoup(await response.text(), 'html.parser')
                    chapter_content = soup.find('div', class_='chapter-c')
                    print(chapter_content)
                    return chapter_content.get_text(separator='\n', strip=True) if chapter_content else None
                else:
                    logger.error(f"Lỗi HTTP {response.status} khi tải chương {link_chuong}")
                    return None
    except aiohttp.ClientError as e:
        logger.error(f"Lỗi khi tải chương {link_chuong}: {e}")
        return None




# Celery tasks
from celery import shared_task
from app_truyen.models import Story, Chapter
from bs4 import BeautifulSoup
import requests
from django.utils import timezone

@shared_task
def fetch_chapter(story_name, chapter_number, crawl_url):
    try:
        story = Story.objects.get(title=story_name)
    except Story.DoesNotExist:
        return {'exists': False, 'error': f"Story '{story_name}' does not exist"}

    chapter_url = f"{crawl_url}/{story_name}/chuong-{chapter_number}"

    try:
        response = requests.get(chapter_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return {'exists': False, 'error': f"Failed to fetch URL {chapter_url}: {str(e)}"}

    soup = BeautifulSoup(response.text, 'html.parser')
    chapter_title = None
    chapter_content = None

    try:
        chapter_title = soup.find('h2').find('a', class_='chapter-title').get_text(strip=True)
        chapter_content_div = soup.find('div', class_='chapter-c')
        chapter_content = chapter_content_div.decode_contents() if chapter_content_div else None
    except AttributeError:
        return {'exists': False, 'error': 'Failed to parse chapter content'}

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
    if not created:
        chapter.title = chapter_title
        chapter.content = chapter_content
        chapter.updated_at = timezone.now()
        chapter.save()

    return {'exists': True, 'chapter': f"{chapter.title} (Chapter {chapter_number})"}
