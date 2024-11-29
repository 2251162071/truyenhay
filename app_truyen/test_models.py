from django.test import TestCase
from app_truyen.models import Story, Genre, Chapter
from django.utils.timezone import now

class GenreModelTest(TestCase):
    def test_genre_save_creates_slug(self):
        genre = Genre.objects.create(name_full="Phiêu Lưu")
        self.assertEqual(genre.name, "phieu-luu")




class StoryModelTest(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name_full="Huyền Huyễn")

    def test_story_save_creates_slug(self):
        story = Story.objects.create(
            title_full="Tiên Nghịch",
            author="Nhĩ Căn",
            status="Đang ra",
            views=1000,
            updated_at=now(),
        )
        self.assertEqual(story.title, "tien-nghich")

    def test_story_genres_relationship(self):
        story = Story.objects.create(
            title_full="Tiên Nghịch",
            author="Nhĩ Căn",
            status="Đang ra",
            views=1000,
            updated_at=now(),
        )
        story.genres.add(self.genre)
        self.assertEqual(story.genres.count(), 1)


class ChapterModelTest(TestCase):
    def setUp(self):
        self.story = Story.objects.create(
            title_full="Tiên Nghịch",
            author="Nhĩ Căn",
            status="Đang ra",
            views=1000,
            updated_at=now(),
        )

    def test_chapter_creation(self):
        chapter = Chapter.objects.create(
            story=self.story,
            title="Chương 1",
            content="Nội dung chương 1",
            chapter_number=1,
            views=100,
            updated_at=now(),
        )
        self.assertEqual(str(chapter), "Chương 1 - Chương 1")

