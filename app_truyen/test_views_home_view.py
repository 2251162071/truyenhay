from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch


class HomeViewTest(TestCase):
    @patch('app_truyen.views.get_hot_stories')
    @patch('app_truyen.views.get_recommend_stories')
    def test_home_view(self, mock_recommend, mock_hot):
        mock_hot.return_value = ['Story 1', 'Story 2']
        mock_recommend.return_value = ['Story 3', 'Story 4']

        response = self.client.get(reverse('home_name'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/home.html')
        self.assertIn('danh_sach_truyen_hot', response.context)
        self.assertIn('danh_sach_truyen_de_cu', response.context)
