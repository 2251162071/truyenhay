from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock
from app_truyen.models import Story, Chapter, Genre, Comment
from django.utils.timezone import now

class HomeViewTest(TestCase):
    @patch("app_truyen.views.get_hot_stories")
    @patch("app_truyen.views.get_recommend_stories")
    def test_home_view(self, mock_recommend_stories, mock_hot_stories):
        mock_hot_stories.return_value = [{"title": "hot-story"}]
        mock_recommend_stories.return_value = [{"title": "recommend-story"}]

        response = self.client.get(reverse("home_name"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home/home.html")
        self.assertIn("danh_sach_truyen_hot", response.context)
        self.assertIn("danh_sach_truyen_de_cu", response.context)

class StoryViewTest(TestCase):
    def setUp(self):
        self.story = Story.objects.create(
            title="tien-nghich",
            title_full="Tiên Nghịch",
            author="Nhĩ Căn",
            status="Đang ra",
            views=1000,
            chapter_number=5,
            updated_at=now(),
        )
        for i in range(1, 6):
            Chapter.objects.create(
                story=self.story,
                title=f"Chương {i}",
                content=f"Nội dung chương {i}",
                chapter_number=i,
                views=0,
                updated_at=now(),
            )

    def test_story_view(self):
        response = self.client.get(reverse("story_detail", kwargs={"story_name": self.story.title}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app_truyen/truyen.html")
        self.assertIn("story", response.context)

    @patch("app_truyen.views.crawl_story")
    def test_story_view_nonexistent_story(self, mock_crawl_story):
        # Mock crawl_story trả về thất bại
        mock_crawl_story.return_value = {'exists': False, 'error': 'Failed to fetch story information'}

        response = self.client.get(reverse("story_detail", kwargs={"story_name": "nonexistent-story"}))
        self.assertEqual(response.status_code, 404)  # Xác nhận trả về 404

class ChapterViewTest(TestCase):
    def setUp(self):
        self.story = Story.objects.create(
            title="tien-nghich",
            title_full="Tiên Nghịch",
            author="Nhĩ Căn",
            status="Đang ra",
            views=1000,
            chapter_number=5,
            updated_at=now(),
        )
        self.chapter = Chapter.objects.create(
            story=self.story,
            title="Chương 1",
            content="Nội dung chương 1",
            chapter_number=1,
            views=10,
            updated_at=now(),
        )

    def test_chapter_view_existing_chapter(self):
        response = self.client.get(reverse("chapter_detail", kwargs={
            "story_name": self.story.title,
            "chapter_number": self.chapter.chapter_number
        }))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app_truyen/chuong.html")
        self.assertIn("current_chapter", response.context)

    def test_chapter_view_nonexistent_chapter(self):
        response = self.client.get(reverse("chapter_detail", kwargs={
            "story_name": self.story.title,
            "chapter_number": 999
        }))
        self.assertEqual(response.status_code, 404)

class GenreViewTest(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name_full="Tiên Hiệp")
        self.story = Story.objects.create(
            title="tien-nghich",
            title_full="Tiên Nghịch",
            author="Nhĩ Căn",
            status="Đang ra",
            views=1000,
            chapter_number=5,
            updated_at=now(),
        )
        self.story.genres.add(self.genre)

    def test_genre_view(self):
        response = self.client.get(reverse("genre_name", kwargs={"the_loai": self.genre.name, "so_trang": 1}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app_truyen/danh_sach_truyen.html")
        self.assertIn("danh_sach_truyen", response.context)

    def test_genre_view_nonexistent_genre(self):
        response = self.client.get(reverse("genre_name", kwargs={"the_loai": "nonexistent-genre", "so_trang": 1}))
        self.assertEqual(response.status_code, 200)  # Đảm bảo trả về trang 404
        self.assertTemplateUsed(response, "404.html")  # Kiểm tra template 404
        self.assertIn("error", response.context)  # Kiểm tra thông báo lỗi trong context
        self.assertEqual(
            response.context["error"],
            "Không tìm thấy truyện nào thuộc thể loại 'nonexistent-genre'."
        )