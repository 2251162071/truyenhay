import requests
from django.core.management.base import BaseCommand

from app_truyen import utils
from app_truyen.models import Story, Chapter
from truyenhay.settings import CRAWL_URL
from django.utils import timezone
from bs4 import BeautifulSoup
import subprocess
import logging
import os
import re

logger = logging.getLogger(__name__)

"""
Insert missing chapters for a given story into the database
chapter_range is optional. If not provided, all chapters from 1 to the last chapter will be added.
python manage.py get_missing_chapters <story_name> --chapter_range <start-end>
python manage.py get_missing_chapters "tien-nghich"
"""
class Command(BaseCommand):
    help = 'Get missing chapters for a given story and add them to the database'

    def add_arguments(self, parser):
        parser.add_argument(
            'story_name',
            type=str,
            help='Name of the story'
        )
        parser.add_argument(
            '--chapter_range',
            type=str,
            help='Range of chapter numbers, e.g., "1-5"',
            required=False
        )

    def handle(self, *args, **kwargs):
        story_name = kwargs['story_name']
        chapter_range = kwargs['chapter_range']

        try:
            try:
                story = Story.objects.get(title=story_name)
            except Story.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Story '{story_name}' does not exist"))
                return

            if not chapter_range:
                start = 1
                end = story.chapter_number
                # self.stdout.write(self.style.ERROR("Chapter range is required"))
                # return
            else:
                start, end = self.parse_range(chapter_range)

            existing_chapters = Chapter.objects.filter(story=story, chapter_number__range=(start, end)).values_list('chapter_number', flat=True)
            missing_chapters = set(range(start, end + 1)) - set(existing_chapters)

            if not missing_chapters:
                self.stdout.write(self.style.SUCCESS(f"All chapters from {start} to {end} already exist in the database."))
                return

            self.stdout.write(f"Missing chapters: {', '.join(map(str, sorted(missing_chapters)))}")

            for chapter_number in sorted(missing_chapters):
                result = utils.crawl_chapter(story_name, chapter_number, CRAWL_URL)
                if result['exists']:
                    # self.stdout.write(self.style.SUCCESS(f"Added chapter {result['chapter']}"))
                    chapter, created = utils.save_or_update_chapter(result['chapter'])
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to add chapter {chapter_number}: {result['error']}"))
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f"Invalid chapter range: {str(e)} chapter_range: {chapter_range}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))

    def parse_range(self, chapter_range):
        """
        Parse the range string into start and end numbers.
        Args:
            chapter_range (str): A string in the format "start-end".

        Returns:
            tuple: A tuple of (start, end).

        Raises:
            ValueError: If the range format is invalid.
        """
        try:
            start, end = map(int, chapter_range.split('-'))
            if start > end:
                raise ValueError("Start of the range cannot be greater than the end.")
            return start, end
        except Exception:
            raise ValueError("Chapter range must be in the format 'start-end' with valid integers.")

    def change_title(self, title):
        pattern = r"(Chương)(\d+)(.*)"
        match = re.search(pattern, title)
        if match:
            return match.group(1) + " " + match.group(2) + match.group(3)
        return title