from django.core.management import call_command
from django.test import TestCase
from app_truyen.models import Genre
from io import StringIO


class InsertGenresCommandTest(TestCase):
    def setUp(self):
        # Tạo một số thể loại trước để kiểm tra cập nhật
        Genre.objects.create(name='tien-hiep', name_full='Tiên Hiệp', page_count=10)
        Genre.objects.create(name='xuyen-khong', name_full='Xuyên Không', page_count=182)

    def test_insert_new_genres(self):
        out = StringIO()
        call_command('insert_genres', stdout=out)

        # Kiểm tra thể loại mới được thêm
        self.assertTrue(Genre.objects.filter(name='ngon-tinh').exists())

        # Kiểm tra thông báo
        self.assertIn('Successfully inserted genre: Ngôn Tình', out.getvalue())

    def test_skip_zero_page_count(self):
        out = StringIO()
        call_command('insert_genres', stdout=out)

        # Kiểm tra thể loại có page_count=0 không được thêm
        self.assertFalse(Genre.objects.filter(name='viet-nam').exists())

        # Kiểm tra thông báo
        self.assertIn('Skipping genre: Việt Nam (page_count=0)', out.getvalue())

    def test_update_existing_genre(self):
        out = StringIO()
        call_command('insert_genres', stdout=out)

        # Kiểm tra thể loại được cập nhật
        genre = Genre.objects.get(name='tien-hiep')
        self.assertEqual(genre.page_count, 48)

        # Kiểm tra thông báo
        self.assertIn('Updated genre: Tiên Hiệp with new page_count', out.getvalue())

    def test_do_not_update_unchanged_genre(self):
        out = StringIO()
        call_command('insert_genres', stdout=out)

        # Kiểm tra thể loại không thay đổi
        genre = Genre.objects.get(name='xuyen-khong')
        self.assertEqual(genre.page_count, 182)

        # Kiểm tra thông báo
        self.assertIn('Genre already exists: Xuyên Không', out.getvalue())
