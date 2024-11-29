# management/commands/import_stories.py
import json
from django.core.management.base import BaseCommand
from app_truyen.models import Story, Genre, StoryGenre
from django.utils import timezone

class Command(BaseCommand):
    help = 'Import stories from a JSON file into the database and update StoryGenre'

    def add_arguments(self, parser):
        # Thêm argument để truyền tên file
        parser.add_argument(
            'file_path',
            type=str,
            help='Path to the JSON file containing stories'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']  # Lấy tên file từ tham số

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for key, value in data.items():
                    story, created = Story.objects.update_or_create(
                        title=value['ten_truyen'],
                        defaults={
                            'title_full': value['ten_truyen_full'] if value.get('ten_truyen_full') else value['ten_truyen'],
                            'author': value['tac_gia'] if value.get('tac_gia') else 'Unknown',
                            'status': value['trang_thai'] if value.get('trang_thai') else 'Unknown',
                            'views': 0,
                            'description': value['description_html'] if value.get('description_html') else '',
                            'image': 'default.webp',
                            'rating': value['rating_value'] if value.get('rating_value') else 0,
                            'chapter_number': value['so_chuong'] if value.get('so_chuong') else 0,
                            'updated_at': timezone.now()
                        }
                    )

                    genre = Genre.objects.filter(name_full=value['the_loai']).first()
                    if genre:
                        StoryGenre.objects.get_or_create(story_id=story.id, genre_id=genre.id)

            self.stdout.write(self.style.SUCCESS('Successfully imported stories and updated StoryGenre'))
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR(f"Invalid JSON format in file: {file_path}"))
