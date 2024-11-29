import unittest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
from app_truyen.utils import (
    crawl_chapter,
    fetch_chapter_content,
    save_or_update_chapter,
    crawl_story,
    calculate_total_chapters,
    extract_text,
    get_status,
    get_description,
    get_rating,
    send_request
)
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truyenhay.settings')
django.setup()

class TestUtils(unittest.TestCase):

    @patch('app_truyen.utils.Story.objects.get')
    @patch('app_truyen.utils.fetch_chapter_content')
    def test_crawl_chapter(self, mock_fetch_chapter_content, mock_get_story):
        # Mock dữ liệu trả về từ fetch_chapter_content
        mock_fetch_chapter_content.return_value = ("Chapter Title", "Chapter Content")

        # Mock dữ liệu truyện
        mock_story = MagicMock()
        mock_story.story_id = 1
        mock_get_story.return_value = mock_story

        result = crawl_chapter("test-story", 1, "https://example.com")
        self.assertTrue(result['exists'])
        self.assertEqual(result['chapter']['title'], "Chapter Title")
        self.assertEqual(result['chapter']['content'], "Chapter Content")

        # Print if test is successful


    @patch('app_truyen.utils.send_request')
    def test_fetch_chapter_content(self, mock_send_request):
        # Mock response cho send_request
        mock_response = MagicMock()
        mock_response.text = '<h2><a class="chapter-title">Chapter Title</a></h2><div class="chapter-c">Content</div>'
        mock_send_request.return_value = mock_response

        title, content = fetch_chapter_content("https://example.com/chapter-1")
        self.assertEqual(title, "Chapter Title")
        self.assertEqual(content, "Content")

    @patch('app_truyen.utils.Chapter.objects.update_or_create')
    def test_save_or_update_chapter(self, mock_update_or_create):
        # Mock kết quả của update_or_create
        mock_chapter = MagicMock()
        mock_update_or_create.return_value = (mock_chapter, True)

        chapter_data = {
            'chapter_number': 1,
            'story_id': MagicMock(story_id=1),
            'title': "Chapter Title",
            'content': "Chapter Content",
            'views': 0,
            'updated_at': "2024-01-01"
        }
        chapter, created = save_or_update_chapter(chapter_data)
        self.assertTrue(created)
        mock_update_or_create.assert_called_once()

    @patch('app_truyen.utils.send_request')
    def test_crawl_story(self, mock_send_request):
        # Mock response cho send_request
        mock_response = MagicMock()
        mock_response.text = '<h3 class="title">Story Title</h3>'
        mock_send_request.return_value = mock_response

        result = crawl_story("https://example.com/story")
        self.assertTrue(result['exists'])
        self.assertEqual(result['story_info']['title_full'], "Story Title")

    def test_extract_text(self):
        html = '<div class="test">Test Text</div>'
        soup = BeautifulSoup(html, 'html.parser')
        text = extract_text(soup, 'div', 'test')
        self.assertEqual(text, "Test Text")

    def test_get_status(self):
        html = '<span class="text-primary">Completed</span>'
        soup = BeautifulSoup(html, 'html.parser')
        status = get_status(soup)
        self.assertEqual(status, "Completed")

    def test_get_description(self):
        html = '<div class="desc-text desc-text-full">Description</div>'
        soup = BeautifulSoup(html, 'html.parser')
        description = get_description(soup)
        self.assertEqual(True, "Description" in description)
        self.assertEqual(True, '<div class="desc-text desc-text-full">' in description)

    def test_get_rating(self):
        html = '<span itemprop="ratingValue">4.5</span>'
        soup = BeautifulSoup(html, 'html.parser')
        rating = get_rating(soup)
        self.assertEqual(rating, 4.5)

    @patch('app_truyen.utils.requests.get')
    def test_send_request(self, mock_get):
        # Mock thành công
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        response = send_request("https://example.com")
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)

    @patch('app_truyen.utils.requests.get')
    def test_calculate_total_chapters(self, mock_get):
        # Mock response
        mock_response = MagicMock()
        mock_response.text = '''
        <ul class="pagination">
            <a href="https://truyenfull.io/story/chuong-1">1</a>
            <a href="https://truyenfull.io/story/chuong-2">2</a>
            <a href="https://truyenfull.io/story/chuong-3">3</a>
        </ul>
        '''
        mock_get.return_value = mock_response

        soup = BeautifulSoup(mock_response.text, 'html.parser')
        total_chapters = calculate_total_chapters(soup, "story")
        self.assertEqual(total_chapters, 3)

if __name__ == '__main__':
    unittest.main()
