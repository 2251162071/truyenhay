from django.core.management import call_command
from django.test import TestCase
from unittest.mock import patch, MagicMock
from app_truyen.models import Story, Chapter
from django.utils import timezone


class GetChapterInfoCommandTest(TestCase):
    def setUp(self):
        # Xóa sạch dữ liệu trước khi tạo mới
        Story.objects.all().delete()
        Chapter.objects.all().delete()
        # Tạo dữ liệu mẫu cho Story
        self.story = Story.objects.create(
            title="sample-story",
            views=0,
            description="Sample Description",
            author="Sample Author",
            status="Sample Status",
            rating=0.0,
            image="https://example.com/image.jpg",
            title_full="Sample Story",
            updated_at=timezone.now()
        )

    @patch('app_truyen.utils.send_request')
    @patch('app_truyen.management.commands.get_chapter_info.BeautifulSoup')
    def test_get_chapter_info_success(self, mock_beautifulsoup, mock_send_request):
        # Mock dữ liệu trả về từ request
        mock_response = MagicMock()
        mock_response.text = """
            <html>
                <h2><a class='chapter-title'>Sample Chapter</a></h2>
                <div class='chapter-c'>Chapter Content</div>
            </html>
        """
        mock_send_request.return_value = mock_response

        # Mock BeautifulSoup
        mock_soup = MagicMock()

        # Mock cấp đầu tiên: soup.find('h2')
        mock_h2_tag = MagicMock()
        # Mock cấp thứ hai: h2.find('a', class_='chapter-title')
        mock_a_tag = MagicMock()
        mock_a_tag.get_text.return_value = "Sample Chapter"  # Định nghĩa get_text()

        # Gán hành vi cho mock
        mock_h2_tag.find.return_value = mock_a_tag  # h2.find() trả về mock_a_tag
        mock_soup.find.side_effect = lambda *args, **kwargs: mock_h2_tag if args == ('h2',) else None

        # Mock cấp tiếp theo: soup.find('div', class_='chapter-c')
        mock_content_div = MagicMock()
        mock_content_div.decode_contents.return_value = "Chapter Content"
        mock_soup.find.side_effect = lambda *args, **kwargs: mock_h2_tag if args == ('h2',) else mock_content_div

        mock_beautifulsoup.return_value = mock_soup

        # Gọi command
        call_command('get_chapter_info', 'sample-story', 1)

        # Kiểm tra Chapter đã được tạo
        chapter = Chapter.objects.get(story=self.story, chapter_number=1)
        self.assertEqual(chapter.title, "Sample Chapter")
        self.assertEqual(chapter.content, "Chapter Content")

    @patch('app_truyen.models.Story.objects.get')
    def test_get_chapter_info_story_not_found(self, mock_story_get):
        # Mock để raise lỗi
        mock_story_get.side_effect = Story.DoesNotExist

        with self.assertRaises(ValueError) as e:
            call_command('get_chapter_info', 'Nonexistent Story', 1)

        self.assertIn("Story 'Nonexistent Story' does not exist", str(e.exception))

    @patch('app_truyen.utils.send_request')
    def test_get_chapter_info_missing_content(self, mock_send_request):
        # Mock dữ liệu trả về từ request
        mock_response = MagicMock()
        mock_response.text = "<html></html>"  # Không có nội dung chương
        mock_send_request.return_value = mock_response

        # Gọi command
        call_command('get_chapter_info', 'Sample Story', 1)

        # Kiểm tra Chapter không được tạo
        self.assertFalse(Chapter.objects.filter(story=self.story, chapter_number=1).exists())
