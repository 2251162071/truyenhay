from unittest.mock import patch, MagicMock
from django.core.management import call_command
from django.test import TestCase

from app_truyen.management.commands.insert_stories_url import Command
from app_truyen.models import Genre, Story, StoryGenre

from truyenhay.settings import CRAWL_URL

class TestCommand(TestCase):
    def setUp(self):
        # Set up initial data
        self.genre = Genre.objects.create(name='tien-hiep', page_count=2)
        self.crawl_url = CRAWL_URL

    @patch('app_truyen.management.commands.insert_stories_url.requests.get')
    def test_handle_genre_not_found(self, mock_requests):
        """
        Test trường hợp thể loại không tồn tại trong database.
        """
        # out = MagicMock()
        # call_command('insert_stories_url', 'khong-ton-tai', stdout=out)
        # out.write.assert_called_with("Thể loại 'khong-ton-tai' không tồn tại trong database.\n")

        with self.assertLogs('app_truyen.management.commands.insert_stories_url', level='ERROR') as cm:
            call_command('insert_stories_url', 'khong-ton-tai')
            self.assertIn("Thể loại 'khong-ton-tai' không tồn tại trong database.", cm.output[0])

    @patch('app_truyen.management.commands.insert_stories_url.requests.get')
    def test_handle_genre_page_count_zero(self, mock_requests):
        """
        Test trường hợp thể loại có page_count bằng 0.
        """
        genre = Genre.objects.create(name='rong', page_count=0)

        with self.assertLogs('app_truyen.management.commands.insert_stories_url', level='ERROR') as cm:
            call_command('insert_stories_url', 'rong')
            self.assertIn("Thể loại 'rong' không có trang nào.", cm.output[0])

    @patch('app_truyen.management.commands.insert_stories_url.requests.get')
    def test_handle_requests_404(self, mock_requests):
        """
        Test trường hợp request trả về 404.
        """
        mock_response = MagicMock(status_code=404)
        mock_requests.return_value = mock_response

        with self.assertLogs('app_truyen.management.commands.insert_stories_url', level='ERROR') as cm:
            call_command('insert_stories_url', 'tien-hiep')
            mock_requests.assert_called_with(f'{self.crawl_url}/the-loai/tien-hiep/trang-1')
            self.assertIn(f"Status Code: 404. Lỗi khi gửi request đến {self.crawl_url}/the-loai/tien-hiep/trang-1",
                          cm.output[0])

    @patch('app_truyen.management.commands.insert_stories_url.requests.get')
    def test_handle_requests_503(self, mock_requests):
        """
        Test trường hợp request trả về 503.
        """
        mock_response = MagicMock(status_code=503)
        mock_requests.return_value = mock_response

        with self.assertLogs('app_truyen.management.commands.insert_stories_url', level='ERROR') as cm:
            call_command('insert_stories_url', 'tien-hiep')
            self.assertIn("Server bị quá tải. Đổi VPN và thử lại sau.", cm.output[0])
            self.assertIn("Đang thử lại...", cm.output[1])

    @patch('app_truyen.management.commands.insert_stories_url.requests.get')
    @patch('app_truyen.management.commands.insert_stories_url.BeautifulSoup')
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

        call_command('insert_stories_url', 'tien-hiep', stdout=out)
        mock_requests.assert_called_with(f'{self.crawl_url}/the-loai/tien-hiep/trang-1')
        out.write.assert_any_call("Save to database: story-1")

    @patch('app_truyen.management.commands.insert_stories_url.requests.get')
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
