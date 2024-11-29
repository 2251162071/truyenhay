from datetime import timezone

from app_truyen.models import Story, Chapter
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch


class StoryViewTest(TestCase):
    def setUp(self):
        self.story = Story.objects.create(
            title="tien-nghich",
            title_full="Tiên Nghịch",
            author="Hồ Điệp",
            status="Đang cập nhật",
            views=0,
            updated_at="2024-11-25 21:16:09.882778 +00:00",
            description="Một thiếu niên từ thế giới hiện đại xuyên không đến thế giới tu tiên, bắt đầu cuộc hành trình tu luyện để trả thù cho",
            rating=4.5,
            image="default.webp",
            chapter_number=10)

    def test_story_view_existing_story(self):
        response = self.client.get(reverse('story_view', kwargs={'story_name': self.story.title}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_truyen/truyen.html')

    def test_story_view_nonexistent_story(self):
        response = self.client.get(reverse('story_view', kwargs={'story_name': 'Nonexistent Story'}))
        self.assertEqual(response.status_code, 404)
