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
