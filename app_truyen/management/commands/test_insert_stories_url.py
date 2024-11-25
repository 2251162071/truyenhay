from unittest.mock import patch, MagicMock
from django.core.management import call_command
from django.test import TestCase

from app_truyen.management.commands.insert_stories_url import Command
from app_truyen.models import Genre, Story, StoryGenre


class TestCommand(TestCase):
    def setUp(self):
        # Set up initial data
        self.genre = Genre.objects.create(name='tien-hiep', page_count=2)
        self.crawl_url = 'http://example.com'

    @patch('app_truyen.management.commands.insert_stories_url.requests.get')
    def test_handle_genre_not_found(self, mock_requests):
        """
        Test trường hợp thể loại không tồn tại trong database.
        """
        out = MagicMock()
        call_command('insert_stories_url', 'khong-ton-tai', stdout=out)
        out.write.assert_called_with("Thể loại 'khong-ton-tai' không tồn tại trong database.")

    @patch('app_truyen.management.commands.crawl_genres.requests.get')
    def test_handle_genre_page_count_zero(self, mock_requests):
        """
        Test trường hợp thể loại có page_count bằng 0.
        """
        genre = Genre.objects.create(name='rong', page_count=0)
        out = MagicMock()
        call_command('crawl_genres', 'rong', stdout=out)
        out.write.assert_called_with(f"Thể loại 'rong' không có trang nào.")

    @patch('app_truyen.management.commands.crawl_genres.requests.get')
    def test_handle_requests_404(self, mock_requests):
        """
        Test trường hợp request trả về 404.
        """
        mock_response = MagicMock(status_code=404)
        mock_requests.return_value = mock_response
        out = MagicMock()

        call_command('crawl_genres', 'tien-hiep', stdout=out)
        mock_requests.assert_called_with(f'{self.crawl_url}/the-loai/tien-hiep/trang-1')
        out.write.assert_called_with(
            "Status Code: 404. Lỗi khi gửi request đến http://example.com/the-loai/tien-hiep/trang-1")

    @patch('app_truyen.management.commands.crawl_genres.requests.get')
    def test_handle_requests_503(self, mock_requests):
        """
        Test trường hợp request trả về 503.
        """
        mock_response = MagicMock(status_code=503)
        mock_requests.return_value = mock_response
        out = MagicMock()

        call_command('crawl_genres', 'tien-hiep', stdout=out)
        out.write.assert_any_call("Server bị quá tải. Đổi VPN và thử lại sau.")
        out.write.assert_any_call("Đang thử lại...")

    @patch('app_truyen.management.commands.crawl_genres.requests.get')
    @patch('app_truyen.management.commands.crawl_genres.BeautifulSoup')
    def test_successful_crawl(self, mock_soup, mock_requests):
        """
        Test trường hợp crawl thành công.
        """
        mock_response = MagicMock(status_code=200,
                                  text='<html><div class="col-truyen-main"><a href="http://example.com/tien-hiep/story-1/"></a></div></html>')
        mock_requests.return_value = mock_response
        mock_soup.return_value.find.return_value.find_all.return_value = [
            {'href': 'http://example.com/tien-hiep/story-1/'}]
        out = MagicMock()

        call_command('crawl_genres', 'tien-hiep', stdout=out)
        mock_requests.assert_called_with(f'{self.crawl_url}/the-loai/tien-hiep/trang-1')
        out.write.assert_any_call("Save to database: story-1")

    @patch('app_truyen.management.commands.crawl_genres.requests.get')
    def test_get_story_info(self, mock_requests):
        """
        Test trường hợp lấy thông tin truyện từ URL.
        """
        mock_response = MagicMock(
            status_code=200,
            text='<html><h3 class="title">Tiên Hiệp</h3><a itemprop="author">Tác giả</a><span itemprop="genre">Thể loại</span></html>'
        )
        mock_requests.return_value = mock_response
        command = Command()
        story_info = command.get_story_info('http://example.com/tien-hiep/story-1/')

        self.assertEqual(story_info['title_full'], 'Tiên Hiệp')
        self.assertEqual(story_info['author'], 'Tác giả')
        self.assertEqual(story_info['genre_full'], 'Thể loại')
