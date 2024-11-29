from unittest.mock import patch, MagicMock
from django.test import TestCase
from app_truyen.tasks import crawl_chapters
from app_truyen.models import Story
from django.utils.timezone import now


class CrawlChaptersTest(TestCase):
    def setUp(self):
        # Tạo dữ liệu mẫu cho test
        self.story = Story.objects.create(
            title="tien-nghich",
            title_full="Tiên Nghịch",
            author="Nhĩ Căn",
            status="Đang ra",
            views=1000,
            chapter_number=10,
            updated_at=now(),
        )

    @patch("app_truyen.tasks.fetch_chapter_content")
    @patch("app_truyen.tasks.save_or_update_chapter")
    def test_crawl_chapters_success(self, mock_save_chapter, mock_fetch_chapter_content):
        # Mock fetch_chapter_content trả về thành công
        mock_fetch_chapter_content.return_value = ("Chapter Title", "Chapter Content")
        # Mock save_or_update_chapter để kiểm tra logic lưu
        mock_save_chapter.return_value = (MagicMock(), True)

        result = crawl_chapters("tien-nghich", 1, 2)

        self.assertEqual(len(result), 2)  # Crawl được 2 chương
        self.assertTrue(mock_save_chapter.called)  # Đảm bảo hàm save_or_update_chapter được gọi

    @patch("app_truyen.tasks.fetch_chapter_content")
    def test_crawl_chapters_fetch_error(self, mock_fetch_chapter_content):
        # Mock fetch_chapter_content trả về lỗi
        mock_fetch_chapter_content.return_value = ("", "")

        result = crawl_chapters("tien-nghich", 1, 2)

        self.assertEqual(len(result), 0)  # Không crawl được chương nào

    def test_crawl_chapters_story_not_found(self):
        # Trường hợp không tìm thấy truyện trong DB
        result = crawl_chapters("nonexistent-story", 1, 2)
        self.assertEqual(len(result), 0)  # Không có chương nào được crawl

    @patch("app_truyen.tasks.fetch_chapter_content")
    def test_crawl_chapters_partial_success(self, mock_fetch_chapter_content):
        # Mock một chương thành công, một chương thất bại
        def mock_fetch(url):
            if "chuong-1" in url:
                return "Chapter 1", "Content 1"
            elif "chuong-2" in url:
                return "", ""

        mock_fetch_chapter_content.side_effect = mock_fetch

        result = crawl_chapters("tien-nghich", 1, 2)

        self.assertEqual(len(result), 1)  # Chỉ crawl được 1 chương
        self.assertEqual(result[0].title, "Chapter 1")

    @patch("app_truyen.tasks.fetch_chapter_content")
    @patch("app_truyen.tasks.save_or_update_chapter")
    def test_crawl_chapters_save_error(self, mock_save_chapter, mock_fetch_chapter_content):
        # Mock fetch thành công
        mock_fetch_chapter_content.return_value = ("Chapter Title", "Chapter Content")
        # Mock save_or_update_chapter gây lỗi
        mock_save_chapter.side_effect = Exception("Database error")

        result = crawl_chapters("tien-nghich", 1, 2)

        self.assertEqual(len(result), 0)  # Không lưu được chương nào
        mock_save_chapter.assert_called()  # Đảm bảo hàm save_or_update_chapter được gọi
