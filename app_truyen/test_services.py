from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from app_truyen.services import (
    get_hot_stories,
    get_recommend_stories,
    get_story_data,
    get_chapters_by_story_name,
    get_chapter_data,
    crawl_chapters_for_story,
)
from app_truyen.models import Story, Chapter, HotStory


class ServicesTest(TestCase):
    def setUp(self):
        # Tạo dữ liệu mẫu
        self.story = Story.objects.create(
            title="tien-nghich",
            title_full="Tiên Nghịch",
            author="Nhĩ Căn",
            status="Đang ra",
            views=1000,
            chapter_number=10,
            updated_at=timezone.now(),
        )

    @patch("app_truyen.services.HotStory.objects.select_related")
    def test_get_hot_stories(self, mock_select_related):
        mock_hot_story = MagicMock()
        mock_hot_story.story = MagicMock(
            title="tien-nghich",
            title_full="Tiên Nghịch",
            author="Nhĩ Căn",
            status="Đang ra",
            views=1000,
            description="A fantasy story",
            rating=4.5,
            image=None  # Giá trị None để kiểm tra logic ảnh mặc định
        )
        mock_select_related.return_value.all.return_value = [mock_hot_story]

        result = get_hot_stories()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], "tien-nghich")
        self.assertEqual(result[0]['title_full'], "Tiên Nghịch")
        self.assertEqual(result[0]['image'], "default_image.jpg")
        self.assertEqual(result[0]['image_path'], "images/default_image.jpg")

    @patch("app_truyen.services.Story.objects.order_by")
    def test_get_recommend_stories(self, mock_order_by):
        # Mock queryset trả về danh sách truyện
        mock_story = MagicMock(
            title="tien-nghich",
            title_full="Tiên Nghịch",
            author="Nhĩ Căn",
            status="Đang ra",
            views=1000,
            description="A fantasy story",
            rating=4.5,
            image="image.jpg"
        )
        mock_order_by.return_value = [mock_story]  # Trả về danh sách mock

        result = get_recommend_stories()
        self.assertEqual(len(result), 1)  # Kiểm tra số lượng truyện trả về
        self.assertEqual(result[0]['title'], "tien-nghich")  # Kiểm tra tiêu đề
        self.assertEqual(result[0]['title_full'], "Tiên Nghịch")  # Kiểm tra tiêu đề đầy đủ
        self.assertEqual(result[0]['image_path'], "images/image.jpg")  # Kiểm tra đường dẫn ảnh

    @patch("app_truyen.services.Story.objects.get")
    def test_get_story_data_success(self, mock_get):
        mock_get.return_value = self.story

        result = get_story_data("tien-nghich")
        self.assertTrue(result['exists'])
        self.assertEqual(result['story'].title, "tien-nghich")

    @patch("app_truyen.services.Story.objects.get")
    def test_get_story_data_not_found(self, mock_get):
        mock_get.side_effect = Story.DoesNotExist

        result = get_story_data("nonexistent-story")
        self.assertFalse(result['exists'])
        self.assertEqual(result['error'], "Story does not exist")

    @patch("app_truyen.services.Story.objects.get")
    @patch("app_truyen.services.Chapter.objects.filter")
    def test_get_chapters_by_story_name(self, mock_filter, mock_get):
        mock_get.return_value = self.story
        mock_chapter = MagicMock(id=1, title="Chapter 1", chapter_number=1)
        mock_filter.return_value.only.return_value = [mock_chapter]

        result = get_chapters_by_story_name("tien-nghich", page_number=1)
        self.assertEqual(len(result['chapters']), 1)
        self.assertEqual(result['chapters'][0].title, "Chapter 1")

    @patch("app_truyen.services.Story.objects.get")
    @patch("app_truyen.services.Chapter.objects.get")
    def test_get_chapter_data_success(self, mock_get_chapter, mock_get_story):
        mock_get_story.return_value = self.story
        mock_chapter = MagicMock(title="Chapter 1", content="Content of Chapter 1")
        mock_get_chapter.return_value = mock_chapter

        result = get_chapter_data("tien-nghich", 1)
        self.assertTrue(result['exists'])
        self.assertEqual(result['title'], "Chapter 1")
        self.assertEqual(result['content'], "Content of Chapter 1")

    @patch("app_truyen.services.Story.objects.get")
    @patch("app_truyen.services.Chapter.objects.get")
    def test_get_chapter_data_not_found(self, mock_get_chapter, mock_get_story):
        mock_get_story.side_effect = Story.DoesNotExist
        mock_get_chapter.side_effect = Chapter.DoesNotExist

        result = get_chapter_data("nonexistent-story", 1)
        self.assertFalse(result['exists'])
        self.assertEqual(result['error'], "Chapter does not exist")

    @patch("app_truyen.services.fetch_chapter_content")
    @patch("app_truyen.services.save_or_update_chapter")
    @patch("app_truyen.services.Story.objects.get")
    def test_crawl_chapters_for_story(self, mock_get_story, mock_save_or_update, mock_fetch_content):
        mock_get_story.return_value = self.story
        mock_fetch_content.return_value = ("Chapter Title", "Chapter Content")
        mock_save_or_update.return_value = (MagicMock(), True)

        crawl_chapters_for_story("tien-nghich", 1, 2)
        self.assertTrue(mock_fetch_content.called)
        self.assertTrue(mock_save_or_update.called)
