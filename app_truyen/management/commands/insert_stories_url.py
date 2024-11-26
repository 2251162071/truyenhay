import logging
import os
import re
import subprocess

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import IntegrityError
from app_truyen.models import Story, Genre, StoryGenre
from truyenhay.settings import CRAWL_URL

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Lấy thông tin truyện thuộc thể loại từ trang web crawl'

    def add_arguments(self, parser):
        parser.add_argument(
            'genre_name',
            type=str,
            help='Thể loại truyện cần lấy thông tin'
        )

    def handle(self, *args, **kwargs):
        genre_name = kwargs['genre_name']
        # Kiểm tra thể loại có tồn tại trong database không
        try:
            genre = Genre.objects.get(name=genre_name)
            logger.info(f"Thể loại '{genre_name}' tồn tại trong database.")
        except Genre.DoesNotExist:
            logger.error(f"Thể loại '{genre_name}' không tồn tại trong database.")
            return

        # Lấy số trang  của thể loại
        page_count = genre.page_count
        if page_count == 0:
            logger.error(f"Thể loại '{genre_name}' không có trang nào.")
            return



        # Lặp qua các trang để lấy thông tin truyện
        for page_number in range(1, page_count + 1):
            page_url = f'{CRAWL_URL}/the-loai/{genre_name}/trang-{page_number}'
            vpn_enabled = self.get_vpn_status(os.getenv('VPN_NAME'))  # Giả sử trạng thái VPN ban đầu là tắt
            while True:
                try:
                    response = requests.get(page_url)
                    if response.status_code == 404:
                        logger.error(f"Status Code: {response.status_code}. Lỗi khi gửi request đến {page_url}")
                        continue
                    elif response.status_code == 503:
                        logger.error(
                            f"Status Code: {response.status_code}. Server bị quá tải. Đổi VPN và thử lại sau.")
                        logger.info(f"VPN status: {'Enabled' if vpn_enabled else 'Disabled'}")
                        vpn_enabled = self.toggle_vpn(vpn_enabled, os.getenv('VPN_NAME'))
                        continue  # Thử lại request sau khi bật/tắt VPN
                    elif response.status_code != 200:
                        logger.error(
                            f"Status Code: {response.status_code}. Lỗi không xác định khi gửi request đến {page_url}")
                        continue
                    response.raise_for_status()
                    break  # Nếu request thành công, thoát khỏi vòng lặp
                except requests.RequestException as e:
                    logger.error(f"Lỗi khi gửi request đến {page_url}: {str(e)}")
                    raise Exception(f"Failed to fetch URL {page_url}: {str(e)}")

            soup = BeautifulSoup(response.text, 'html.parser')
            # Lấy links của các truyện thuộc thể loại trong trang này.
            # Find all <div> tags with class 'text-center pagination-container'
            links = [a['href'] for a in soup.find('div', class_='col-truyen-main').find_all('a', href=True)]

            pattern = r'^https?://[^/]+/[^/]+/$'
            story_links = [link for link in links if re.match(pattern, link)]
            for story_link in story_links:
                # Kiểm tra link_truyện nếu trong link có dấu cách thì sửa lại link (xóa dấu cách)
                if ' ' in story_link:
                    story_link = story_link.replace(' ', '')
                title = story_link.split('/')[-2]
                story_info = self.get_story_info(story_link)
                title_full = story_info["title_full"]
                genre_full = story_info["genre_full"]
                author = story_info["author"]
                status = story_info["status"]
                chapter_number = story_info["chapter_number"]
                description = story_info["description"]
                rating = story_info["rating"]
                views = 0
                image = title + '.jpg'

                # self.stdout.write(self.style.SUCCESS(f"Save to database: {title_full}"))

                self.save_or_update_story(
                    title=title,
                    title_full=title_full,
                    author=author,
                    status=status,
                    genre_full=genre_full,
                    description=description,
                    rating=rating,
                    chapter_number=chapter_number,
                    views=views,
                    image=image,
                    updated_at=timezone.now()
                )

    def get_story_info(self, story_link):
        """
            Lấy thông tin truyện từ URL của truyện.

            Args:
                url (str): URL của truyện cần lấy thông tin.
                'https://example.com/ten-truyen/'

            Returns:
                dict: Thông tin truyện từ URL.
                {'ten_truyen_full': 'Tên truyện', 'tac_gia': 'Tác giả', 'the_loai': 'Thể loại', 'trang_thai': 'Trạng thái', 'so_chuong': 'Số chương', 'description_html': 'Mô tả truyện', 'rating_value': 'Đánh giá'}
            """

        vpn_enabled = self.get_vpn_status(os.getenv('VPN_NAME'))  # Giả sử trạng thái VPN ban đầu là tắt
        while True:
            try:
                response_story = requests.get(story_link, timeout=10)
                if response_story.status_code == 404:
                    logger.error(f"Status Code: {response_story.status_code}. Lỗi khi gửi request đến {story_link}")
                    continue
                elif response_story.status_code == 503:
                    logger.error(f"Status Code: {response_story.status_code}. Server bị quá tải. Đổi VPN và thử lại sau.")
                    logger.info(f"VPN status: {'Enabled' if vpn_enabled else 'Disabled'}")
                    vpn_enabled = self.toggle_vpn(vpn_enabled, os.getenv('VPN_NAME'))
                    continue  # Thử lại request sau khi bật/tắt VPN
                elif response_story.status_code != 200:
                    logger.error(
                        f"Status Code: {response_story.status_code}. Lỗi không xác định khi gửi request đến {story_link}")
                    continue
                response_story.raise_for_status()
                break  # Nếu request thành công, thoát khỏi vòng lặp
            except requests.RequestException as e:
                logger.error(f"Lỗi khi gửi request đến {story_link}: {str(e)}")
                raise Exception(f"Failed to fetch URL {story_link}: {str(e)}")


        soup_story = BeautifulSoup(response_story.text, 'html.parser')
        if soup_story is None:
            logger.error(f"Không thể parse HTML từ {story_link}")
            return None


        title_full = None
        if soup_story.find('h3', class_='title') is not None:
            title_full = soup_story.find('h3', class_='title').get_text(strip=True)
        else:
            title_full = 'Untitled Story'
        author = None
        if soup_story.find('a', {'itemprop': 'author'}) is not None:
            author = soup_story.find('a', {'itemprop': 'author'}).get_text(strip=True)
        else:
            author = 'Unknown'

        if soup_story.find('a', {'itemprop': 'genre'}):
            genre_full = soup_story.find('a', {'itemprop': 'genre'}).get_text(strip=True)
        else:
            genre_full = 'Unknown'
        status = None
        if soup_story.find('span', class_='text-primary') is not None:
            status = soup_story.find('span', class_='text-primary').get_text(strip=True)
        elif soup_story.find('span', class_='text-success') is not None:
            status = soup_story.find('span', class_='text-success').get_text(strip=True)
        elif soup_story.find('span', class_='label-hot') is not None:
            status = 'Hot'
        else:
            status = 'Unknown'
        chapter_number = self.get_chapter_number(soup_story, title_full)
        if soup_story.find('div', class_='desc-text desc-text-full') is None:
            description = soup_story.find('div', {'itemprop': 'description'}).prettify()
        else:
            description = soup_story.find('div', class_='desc-text desc-text-full').prettify()

        rating_tag = soup_story.find("span", itemprop="ratingValue")
        rating_value = float(rating_tag.text) if rating_tag else 0.0
        story_info = {
            "title_full": title_full,
            "author": author,
            "status": status,
            "genre_full": genre_full,
            "chapter_number": chapter_number,
            "description": description,
            "rating": rating_value
        }
        return story_info

    def save_or_update_story(self,
                             title,
                             title_full,
                             author,
                             status,
                             genre_full,
                             description,
                             rating,
                             chapter_number,
                             views,
                             image,
                             updated_at):
        """
        Lưu hoặc cập nhật chapter trong database.
        """
        # Kiểm tra dữ liệu đầu vào
        errors = []

        if not title or not isinstance(title, str):
            errors.append("Title is required and must be a string.")
        if not title_full or not isinstance(title_full, str):
            errors.append("Full title is required and must be a string.")
        if not author or not isinstance(author, str):
            errors.append("Author is required and must be a string.")
        if not isinstance(rating, (int, float)) or rating < 0:
            errors.append("Rating must be a positive number.")
        if not isinstance(chapter_number, int) or chapter_number < 0:
            errors.append("Chapter number must be a non-negative integer.")
        if not isinstance(views, int) or views < 0:
            errors.append("Views must be a non-negative integer.")
        if not updated_at:
            errors.append("Updated_at is required and must be a valid datetime object.")

        # Nếu có lỗi, log lại và thoát sớm
        if errors:
            logger.error(f"Input validation failed: {errors}")
            return None, False

        try:
            # Lưu hoặc cập nhật story
            story, created = Story.objects.update_or_create(
                title=title,
                defaults={
                    'title_full': title_full,
                    'author': author,
                    'status': status,
                    'description': description,
                    'rating': rating,
                    'chapter_number': chapter_number,
                    'views': views,
                    'image': image,
                    'updated_at': updated_at
                }
            )

            if created:
                logger.info(f"Đã lưu truyện '{title_full}' vào database.")
            else:
                logger.info(f"Đã cập nhật thông tin truyện '{title_full}' trong database.")

            # Xử lý thể loại
            genre = Genre.objects.filter(name_full=genre_full).first()
            if genre:
                StoryGenre.objects.get_or_create(story_id=story.id, genre_id=genre.id)
                logger.info(f"Đã lưu thể loại '{genre_full}' cho truyện '{title_full}' vào database.")
            else:
                logger.warning(
                    f"Không tìm thấy thể loại '{genre_full}' trong database. Bỏ qua liên kết với truyện '{title_full}'.")

            return story, created

        except IntegrityError as e:
            logger.error(f"Lỗi ràng buộc database khi lưu truyện '{title_full}': {str(e)}")
        except Exception as e:
            logger.error(f"Lỗi không xác định khi lưu truyện '{title_full}': {str(e)}")

        return None, False

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
            pattern2 = rf'{CRAWL_URL}/{story_name}/quyen-(\d+)-chuong-(\d+)'  # Định dạng "quyen-x-chuong-y"
            numbers = []
            page_numbers = []
            if pagination is not None:
                # Tìm tất cả các thẻ li bên trong ul, rồi lặp qua từng thẻ li để tìm thẻ a có nội dung "Cuối"
                link_cuoi = None
                for li in pagination.find_all('li'):
                    a_tag = li.find('a')
                    if a_tag and "Cuối" in a_tag.get_text():
                        link_cuoi = a_tag['href']
                        break  # Dừng lại nếu đã tìm thấy
                if link_cuoi is None:
                    for li in pagination.find_all('li'):
                        a_tag = li.find('a')
                        if a_tag:
                            if a_tag.get_text().isnumeric():
                                page_numbers.append(int(a_tag.get_text()))
                    last_page = max(page_numbers)
                    link_cuoi = f'{CRAWL_URL}/{story_name}/trang-{last_page}/#list-chapter'


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
                        match = re.search(pattern2, link['href'])
                        if match:
                            pattern3 = r'chuong-(\d+)'
                            match3 = re.search(pattern3, link['href'])
                            number = int(match3.group(1))
                            numbers.append(number)
            else:
                for link in soup.find_all('a', href=True):
                    match = re.search(pattern, link['href'])
                    if match:
                        number = int(match.group(1))  # Lấy số x và chuyển thành integer
                        numbers.append(number)
                    else:
                        match = re.search(pattern2, link['href'])
                        if match:
                            pattern3 = r'chuong-(\d+)'
                            match3 = re.search(pattern3, link['href'])
                            number = int(match3.group(1))
                            numbers.append(number)

            # Tìm số lớn nhất
            so_chuong = max(numbers) if numbers else 0
            # story = Story.objects.get(title=story_name)
            # story.chapter_number = so_chuong
            # story.save()
            return so_chuong
        except Exception as e:
            return 0