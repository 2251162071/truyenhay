from django.test import TestCase, Client
from django.utils import timezone
from decimal import Decimal
from django.core.cache import cache
from django.urls import reverse
from .models import Genre, Story, StoryGenre, Chapter, UserReading, HotStory, NewUpdatedStory
from .views import CRAWL_STATUS_KEY
from unittest.mock import patch

class GenreModelTest(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name_full="Tiên hiệp")

    def test_genre_name_slug_creation(self):
        self.assertEqual(self.genre.name, "tien-hiep")

    def test_genre_str(self):
        self.assertEqual(str(self.genre), "Tiên hiệp")

    def test_default_page_count(self):
        self.assertEqual(self.genre.page_count, 0)


class StoryModelTest(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name_full="Tiên hiệp")
        self.story = Story.objects.create(
            title_full="Truyện test",
            author="Tác giả",
            status="Hoàn thành",
            views=100,
            updated_at=timezone.now(),
            rating=Decimal('4.50'),
            description="Mô tả truyện",
        )
        self.story.genres.add(self.genre)

    def test_story_title_slug_creation(self):
        self.assertEqual(self.story.title, "truyen-test")

    def test_story_str(self):
        self.assertEqual(str(self.story), "Truyện test")

    def test_story_genre_relationship(self):
        self.assertIn(self.genre, self.story.genres.all())

    def test_story_default_chapter_number(self):
        self.assertEqual(self.story.chapter_number, 0)


class ChapterModelTest(TestCase):
    def setUp(self):
        self.story = Story.objects.create(
            title_full="Truyện test",
            author="Tác giả",
            status="Hoàn thành",
            views=100,
            updated_at=timezone.now(),
        )
        self.chapter = Chapter.objects.create(
            story=self.story,
            title="Chương 1",
            content="Nội dung chương 1",
            chapter_number=1,
            views=50,
            updated_at=timezone.now(),
        )

    def test_chapter_str(self):
        self.assertEqual(str(self.chapter), "Chương 1 - Chương 1")

    def test_chapter_story_relationship(self):
        self.assertEqual(self.chapter.story, self.story)


class UserReadingModelTest(TestCase):
    def setUp(self):
        self.story = Story.objects.create(
            title_full="Truyện test",
            author="Tác giả",
            status="Hoàn thành",
            views=100,
            updated_at=timezone.now(),
        )
        self.chapter = Chapter.objects.create(
            story=self.story,
            title="Chương 1",
            content="Nội dung chương 1",
            chapter_number=1,
            views=50,
            updated_at=timezone.now(),
        )
        self.user_reading = UserReading.objects.create(
            user_id=1,
            story=self.story,
            last_chapter=self.chapter,
            last_read_at=timezone.now(),
        )

    def test_user_reading_relationship(self):
        self.assertEqual(self.user_reading.story, self.story)
        self.assertEqual(self.user_reading.last_chapter, self.chapter)


class HotStoryModelTest(TestCase):
    def setUp(self):
        self.story = Story.objects.create(
            title_full="Truyện hot",
            author="Tác giả",
            status="Hot",
            views=1000,
            updated_at=timezone.now(),
        )
        self.hot_story = HotStory.objects.create(story=self.story, added_at=timezone.now())

    def test_hot_story_relationship(self):
        self.assertEqual(self.hot_story.story, self.story)


class NewUpdatedStoryModelTest(TestCase):
    def setUp(self):
        self.story = Story.objects.create(
            title_full="Truyện mới",
            author="Tác giả",
            status="Mới",
            views=500,
            updated_at=timezone.now(),
        )
        self.new_updated_story = NewUpdatedStory.objects.create(story=self.story, added_at=timezone.now())

    def test_new_updated_story_relationship(self):
        self.assertEqual(self.new_updated_story.story, self.story)



from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from unittest.mock import patch, MagicMock
from .models import Story, Chapter, Genre

class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Tạo dữ liệu mẫu
        self.story = Story.objects.create(title="Truyen A", title_full="Truyện A Full", views=500, author="Tác giả", status="Hoàn thành", updated_at="2024-11-25 00:12:08.581155+07", chapter_number=10)
        self.chapter = Chapter.objects.create(
            story=self.story, chapter_number=1, title="Chapter 1", views=1000, updated_at="2024-11-25 00:12:08.581155+07", content="Nội dung chương 1"
        )
        self.genre = Genre.objects.create(name="Tiên Hiệp")
        self.genre.stories.add(self.story)
        cache.clear()

    def test_home_view(self):
        response = self.client.get(reverse('home_name'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/home.html')

    def test_story_view_found(self):
        response = self.client.get(reverse('story_detail', args=[self.story.title]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_truyen/truyen.html')
        self.assertContains(response, self.story.title_full)

    def test_story_view_not_found(self):
        response = self.client.get(reverse('story_detail', args=["khong-co-truyen"]))
        self.assertEqual(response.status_code, 200)

    @patch('app_truyen.views.crawl_chapters_async')
    def test_story_view_crawling(self, mock_crawl_chapters_async):
        # Xóa tất cả chương
        Chapter.objects.all().delete()
        cache.set(f"crawl_status_{self.story.title}", True, timeout=600)

        response = self.client.get(reverse('story_detail', args=[self.story.title]))
        self.assertEqual(response.status_code, 202)
        self.assertJSONEqual(response.content, {
            'status': 'crawling',
            'message': 'Đang tải danh sách chương, vui lòng đợi...'
        })

    def test_crawl_status_view(self):
        cache.set(f"crawl_status_{self.story.title}", True)
        response = self.client.get(reverse('crawl_status_view', args=[self.story.title]))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'crawling': True})

    def test_chapter_view_found(self):
        response = self.client.get(reverse('chapter_view', args=[self.story.title, 1]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_truyen/chuong.html')
        self.assertContains(response, self.chapter.title)

    def test_chapter_view_not_found(self):
        response = self.client.get(reverse('chapter_view', args=[self.story.title, 999]))
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')

    def test_genre_view_found(self):
        response = self.client.get(reverse('genre_view', args=["Tiên Hiệp", 1]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_truyen/danh_sach_truyen.html')
        self.assertContains(response, self.story.title)

    def test_genre_view_not_found(self):
        response = self.client.get(reverse('genre_view', args=["Không Có", 1]))
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        self.assertContains(response, "Không tìm thấy truyện nào")

    def test_genre_view_pagination(self):
        response = self.client.get(reverse('genre_view', args=["Tiên Hiệp", 1]))
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertIn('danh_sach_truyen', context)
        self.assertTrue(context['has_next'] or context['has_prev'])

    @patch('app_truyen.views.crawl_chapters_async')
    def test_story_view_crawl_error(self, mock_crawl_chapters_async):
        mock_crawl_chapters_async.side_effect = Exception("Mocked exception")
        Chapter.objects.all().delete()

        response = self.client.get(reverse('story_view', args=[self.story.title]))
        self.assertEqual(response.status_code, 500)
        self.assertJSONEqual(response.content, {
            'status': 'error',
            'message': 'Lỗi trong quá trình crawl dữ liệu.'
        })


from django.test import TestCase
from unittest.mock import patch, MagicMock
from .models import Story, Chapter, Genre, HotStory
from .services import (
    get_hot_stories,
    get_story_data,
    get_chapters_by_story_name,
    get_chapter_data,
    crawl_chapters_for_story,
    get_stories_by_genre,
    crawl_chapters
)

class ServicesTest(TestCase):
    def setUp(self):
        # Tạo dữ liệu mẫu
        self.story = Story.objects.create(title="Truyen A", author="Author A", status="Full", views=100,updated_at="2024-11-25 00:12:08.581155+07", description="Description",title_full="Truyen A Full", rating=4.5, image="image.png", chapter_number=100)
        self.chapter = Chapter.objects.create(story=self.story, chapter_number=1, title="Chapter 1", views=10, updated_at="2024-11-25 00:12:08.581155+07", content="Content of chapter 1")
        self.genre = Genre.objects.create(name="tien-hiep", name_full="Tiên Hiệp", page_count=8)
        self.genre.stories.add(self.story)
        self.hot_story = HotStory.objects.create(story=self.story, added_at="2024-11-25 00:12:08.581155+07")

    def test_get_hot_stories(self):
        hot_stories = get_hot_stories()
        self.assertEqual(len(hot_stories), 1)
        self.assertEqual(hot_stories[0]['title'], self.story.title)

    def test_get_story_data_found(self):
        result = get_story_data("Truyen A")
        self.assertTrue(result['exists'])
        self.assertEqual(result['story'], self.story)

    def test_get_story_data_not_found(self):
        result = get_story_data("Nonexistent Story")
        self.assertFalse(result['exists'])
        self.assertEqual(result['error'], "Story does not exist")

    def test_get_chapters_by_story_name_found(self):
        result = get_chapters_by_story_name("Truyen A", page_number=1)
        self.assertIn(self.chapter, result['chapters'])

    def test_get_chapters_by_story_name_not_found(self):
        result = get_chapters_by_story_name("Nonexistent Story", page_number=1)
        self.assertIn('error', result)
        self.assertEqual(result['error'], "Story does not exist")

    def test_get_chapter_data_found(self):
        result = get_chapter_data("Truyen A", 1)
        self.assertTrue(result['exists'])
        self.assertEqual(result['title'], self.chapter.title)
        self.assertEqual(result['content'], self.chapter.content)

    def test_get_chapter_data_not_found(self):
        result = get_chapter_data("Truyen A", 999)
        self.assertFalse(result['exists'])
        self.assertEqual(result['error'], "Chapter does not exist")

    @patch('app_truyen.services.get_chapter_content')
    def test_crawl_chapters_for_story(self, mock_get_chapter_content):
        mock_get_chapter_content.return_value = ("Content of chapter 1", "Chapter 1")
        crawl_chapters_for_story("Truyen A", page_number=1)
        self.assertTrue(Chapter.objects.filter(chapter_number=1).exists())

    def test_get_stories_by_genre_found(self):
        result = get_stories_by_genre("tien-hiep")
        self.assertIn(self.story, result)

    def test_get_stories_by_genre_not_found(self):
        result = get_stories_by_genre("Nonexistent Genre")
        self.assertIsNone(result)

    @patch('app_truyen.services.get_chapter_content')
    def test_crawl_chapters(self, mock_get_chapter_content):
        mock_get_chapter_content.return_value = ("Content of chapter", "Chapter Title")
        crawl_chapters("Truyen A", start_chapter=2, end_chapter=3)
        self.assertTrue(Chapter.objects.filter(chapter_number=2).exists())
        self.assertTrue(Chapter.objects.filter(chapter_number=3).exists())

    @patch('app_truyen.services.get_chapter_content')
    def test_crawl_chapters_invalid_range(self, mock_get_chapter_content):
        with self.assertLogs('app_truyen.services', level='ERROR') as log:
            crawl_chapters("Truyen A", start_chapter=3, end_chapter=2)
            self.assertIn("Invalid chapter range", log.output[0])

    def test_crawl_chapters_for_nonexistent_story(self):
        with self.assertLogs('app_truyen.services', level='ERROR') as log:
            crawl_chapters("Nonexistent Story", start_chapter=1)
            self.assertIn("Story Nonexistent Story does not exist", log.output[0])
