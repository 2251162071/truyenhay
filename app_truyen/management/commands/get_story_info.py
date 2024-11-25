import re

import requests
from bs4 import BeautifulSoup
from celery.bin.control import status
from django.core.management.base import BaseCommand
from django.template.defaultfilters import title
from django.utils import timezone
from app_truyen import utils
from app_truyen.models import Story, Genre, StoryGenre
from truyenhay.settings import CRAWL_URL
import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Get story information from a given URL and save it to the database'

    def add_arguments(self, parser):
        parser.add_argument(
            'story_url',
            type=str,
            help='URL to get story info'
        )

    def handle(self, *args, **kwargs):
        story_url = kwargs['story_url']
        story_info = self.get_story_info(story_url)
        if story_info:
            self.stdout.write(self.style.SUCCESS(f"Story information: {story_info}"))
            self.save_story_to_db(story_info)
        else:
            self.stdout.write(self.style.ERROR("Failed to get story information."))

    def get_story_info(self, story_name):
        try:
            url = f"{CRAWL_URL}/{story_name}"
            response = utils.send_request(url)
            if response.status_code == 404:
                logger.error(f"[lay_thong_tin_truyen] Có lỗi 404 {response.status_code}")
                return None
            soup = BeautifulSoup(response.text, 'html.parser')

            title_full = self.get_title_full(soup)
            author = self.get_author(soup)
            genre = self.get_genre(soup)
            status_story = self.get_status(soup)
            chapter_number = self.get_chapter_number(soup, story_name)
            description = self.get_description(soup)
            rating = self.get_rating(soup)
            views = self.get_views(soup)
            updated_at = self.get_updated_at()

            story_info = {
                "title": story_name,
                "author": author,
                "status": status_story,
                "views": views,
                "updated_at": updated_at,
                "description": description,
                "image": 'default.webp',
                "title_full": title_full,
                "rating": rating,
                "chapter_number": chapter_number,
                "genre": genre,
            }
            return story_info
        except requests.RequestException as e:
            logger.error(f"Lỗi khi lấy thông tin truyện từ {url}: {e}", 'red')
            return None

    def get_title(self, url):
        return url.split('/')[-1]

    def get_title_full(self, soup):
        title = soup.find('h3', class_='title')
        if title:
            return title.get_text(strip=True)
        return None

    def get_author(self, soup):
        author = soup.find('a', {'itemprop': 'author'})
        if author:
            return author.get_text(strip=True)
        return None

    def get_genre(self, soup):
        genre = soup.find('a', {'itemprop': 'genre'})
        if genre:
            return genre.get_text(strip=True)
        return None

    def get_status(self, soup):
        status = soup.find('span', class_='text-primary')
        if not status:
            status = soup.find('span', class_='text-success')
        if not status:
            status = soup.find('span', 'label-hot')
        if status:
            return status.get_text(strip=True)
        return None

    def get_chapter_number(self, soup, story_name):
        """
            Get the total number of chapters of a story with the given name.

            Args:
                request: The HTTP request object.
                story_name (str): The name of the story.

            Returns:
                JsonResponse: A JSON response with the total number of chapters if the story exists, otherwise an error message.
            """
        try:
            # Tìm thẻ ul có class pagination
            pagination = soup.find('ul', class_='pagination')
            # Regex để tìm số x trong định dạng "chuong-x"
            pattern = rf'{CRAWL_URL}/{story_name}/chuong-(\d+)'
            numbers = []
            if pagination is not None:
                # Tìm tất cả các thẻ li bên trong ul, rồi lặp qua từng thẻ li để tìm thẻ a có nội dung "Cuối"
                link_cuoi = None
                for li in pagination.find_all('li'):
                    a_tag = li.find('a')
                    if a_tag and "Cuối" in a_tag.get_text():
                        link_cuoi = a_tag['href']
                        break  # Dừng lại nếu đã tìm thấy
                # Gửi request đến link đã tìm được
                response = requests.get(link_cuoi)
                response.raise_for_status()  # Kiểm tra lỗi kết nối

                # Phân tích HTML bằng BeautifulSoup
                so_chuong_soup = BeautifulSoup(response.text, 'html.parser')

                # Duyệt qua từng thẻ <a> và lấy số x
                for link in so_chuong_soup.find_all('a', href=True):
                    match = re.search(pattern, link['href'])
                    if match:
                        number = int(match.group(1))  # Lấy số x và chuyển thành integer
                        numbers.append(number)
            else:
                for link in soup.find_all('a', href=True):
                    match = re.search(pattern, link['href'])
                    if match:
                        number = int(match.group(1))  # Lấy số x và chuyển thành integer
                        numbers.append(number)

            # Tìm số lớn nhất
            so_chuong = max(numbers) if numbers else 0
            # story = Story.objects.get(title=story_name)
            # story.chapter_number = so_chuong
            # story.save()
            return so_chuong
        except Exception as e:
            return 0

    def get_description(self, soup):
        description = soup.find('div', class_='desc-text desc-text-full')
        if description:
            return description.prettify()
        description = soup.find('div', {'itemprop': 'description'})
        if description:
            return description.prettify()
        return None

    def get_rating(self, soup):
        rating_tag = soup.find("span", itemprop="ratingValue")
        if rating_tag:
            return float(rating_tag.text)
        return 0.0

    def get_views(self, soup):
        return 0

    def get_updated_at(self):
        return timezone.now()

    def save_story_to_db(self, story_info):
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
            self.stdout.write(self.style.SUCCESS(f"Successfully saved story: {story_info['title_full']}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully updated story: {story_info['title_full']}"))

        genre = Genre.objects.filter(name_full=story_info['genre']).first()
        if genre:
            StoryGenre.objects.get_or_create(story_id=story.id, genre_id=genre.id)