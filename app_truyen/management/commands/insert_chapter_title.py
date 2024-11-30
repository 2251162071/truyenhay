# -*- coding: utf-8 -*-

import json
from django.utils import timezone

from django.core.management.base import BaseCommand
from app_truyen.models import Chapter  # Đảm bảo model của bạn được import đúng

class Command(BaseCommand):
    help = 'Import chapters from a JSON file into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', type=str, help='Path to the JSON file containing chapter data'
        )

    def handle(self, *args, **kwargs):
        file_path = kwargs['file']
        if not file_path:
            self.stderr.write(self.style.ERROR('Please provide a file path using --file'))
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                chapters = json.load(f)

            for chapter_data in chapters:
                Chapter.objects.create(
                    title=chapter_data['title'],
                    content=chapter_data['content'],
                    chapter_number=chapter_data['chapter_number'],
                    views=chapter_data['views'],
                    story_id=chapter_data['story_id'],  # Thay bằng ForeignKey nếu cần
                    updated_at=timezone.now()
                )
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(chapters)} chapters'))
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'File not found: {file_path}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error occurred: {e}'))
