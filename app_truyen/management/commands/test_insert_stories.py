import os
import json
from django.core.management import call_command
from django.test import TestCase
from app_truyen.models import Story, Genre, StoryGenre

class InsertStoriesCommandTest(TestCase):
    def setUp(self):
        # Tạo file JSON giả để kiểm tra
        self.test_json_file = 'test_stories.json'
        self.sample_data = [
            {
                "Title": "Test Story 1",
                "Author": "Author 1",
                "Image": "https://example.com/image1.jpg",
                "Info": "Chương 50",
                "Genres": "Tiên Hiệp, Huyền Huyễn"
            },
            {
                "Title": "Test Story 2",
                "Author": "Author 2",
                "Image": "https://example.com/image2.jpg",
                "Info": "Chương 30",
                "Genres": "Ngôn Tình"
            }
        ]
        with open(self.test_json_file, 'w', encoding='utf-8') as f:
            json.dump(self.sample_data, f)

    def tearDown(self):
        # Xóa file JSON sau khi kiểm tra
        if os.path.exists(self.test_json_file):
            os.remove(self.test_json_file)

    def test_import_stories_command(self):
        # Gọi lệnh import_stories
        call_command('insert_stories', self.test_json_file, "tien-hiep")

        # Kiểm tra dữ liệu được import đúng
        self.assertEqual(Story.objects.count(), 2)
        self.assertEqual(Genre.objects.count(), 3)  # Tiên Hiệp, Huyền Huyễn, Ngôn Tình
        self.assertEqual(StoryGenre.objects.count(), 3)  # Liên kết giữa story và genres

        # Kiểm tra story đầu tiên
        story1 = Story.objects.get(title_full="Test Story 1")
        self.assertEqual(story1.author, "Author 1")
        self.assertEqual(story1.image, "https://example.com/image1.jpg")
        self.assertEqual(story1.chapter_number, 50)

        # Kiểm tra genres của story1
        genres_story1 = [genre.name_full for genre in story1.genres.all()]
        self.assertIn("Tiên Hiệp", genres_story1)
        self.assertIn("Huyền Huyễn", genres_story1)

        # Kiểm tra story thứ hai
        story2 = Story.objects.get(title_full="Test Story 2")
        self.assertEqual(story2.author, "Author 2")
        self.assertEqual(story2.image, "https://example.com/image2.jpg")
        self.assertEqual(story2.chapter_number, 30)

        # Kiểm tra genres của story2
        genres_story2 = [genre.name_full for genre in story2.genres.all()]
        self.assertIn("Ngôn Tình", genres_story2)


    def test_import_with_existing_genre(self):
        genre = Genre.objects.create(name="tien-hiep", name_full="Tiên Hiệp")

        call_command('import_stories', self.test_json_file, "tien-hiep")

        # Kiểm tra Genre không thay đổi
        self.assertEqual(Genre.objects.count(), 1)
        self.assertEqual(genre.name_full, "Tiên Hiệp")

        # Kiểm tra Story được tạo/cập nhật
        story1 = Story.objects.get(title="test-story-1")
        self.assertEqual(story1.title_full, "Test Story 1")
        self.assertEqual(story1.chapter_number, 50)

        # Kiểm tra liên kết trong StoryGenre
        story_genre = StoryGenre.objects.filter(story=story1, genre=genre)
        self.assertTrue(story_genre.exists())

    def test_import_with_nonexistent_genre(self):
        # Gọi lệnh với một thể loại không tồn tại
        with self.assertRaises(SystemExit):
            call_command('import_stories', self.test_json_file, "nonexistent-genre")

        # Đảm bảo không có dữ liệu được tạo
        self.assertEqual(Story.objects.count(), 0)
        self.assertEqual(Genre.objects.count(), 0)
        self.assertEqual(StoryGenre.objects.count(), 0)
