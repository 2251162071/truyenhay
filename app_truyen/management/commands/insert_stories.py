import json
import re
from urllib.parse import urlparse
from django.core.management.base import BaseCommand
from app_truyen.models import Story, Genre, StoryGenre
from django.utils import timezone


"""
Insert stories from a JSON file into the database and link them with a specific genre
python manage.py insert_stories <json_file:app_truyen\\management\\commands\\tien-nghich.json> <genre_name:tien-nghich>
"""
class Command(BaseCommand):
    help = 'Import stories and link them with a specific genre from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file')
        parser.add_argument('genre_name', type=str, help='Genre name to link stories with')

    def handle(self, *args, **options):
        json_file = options['json_file']
        genre_name = options['genre_name']

        try:
            # Get thể loại
            try:
                genre = Genre.objects.get(name=genre_name)
                self.stdout.write(f"Using existing genre: {genre.name_full}")
            except Genre.DoesNotExist:
                self.stderr.write(f"====[ERROR]====Genre '{genre_name}' does not exist!")
                return

            # Đọc file JSON
            with open(json_file, 'r', encoding='utf-8') as file:
                data = json.load(file)

            for entry in data:
                # Lấy phần slug từ Title_URL
                title_url = entry.get("Title_URL", "")
                parsed_url = urlparse(title_url)
                title_slug = parsed_url.path.strip("/").split("/")[-1]

                # Xử lý chapter_number từ trường Info
                chapter_info = entry.get("Info", "")
                chapter_number_match = re.search(r'\d+', chapter_info)
                chapter_number = int(chapter_number_match.group()) if chapter_number_match else 0

                # Cập nhật hoặc tạo Story
                story, created = Story.objects.update_or_create(
                    title=title_slug,  # Sử dụng slug từ Title_URL
                    defaults={
                        'title_full': entry.get("Title", "noname"),
                        'author': entry.get("Author", "unknown").strip(),
                        'status': "Full",
                        'views': 0,
                        'updated_at': timezone.now(),
                        'image': entry.get("Image", "").strip(),
                        'rating': 0.00,
                        'description': None,
                        'chapter_number': chapter_number,
                    }
                )
                action = "Created" if created else "Updated"
                self.stdout.write(f"{action} Story: {story.title_full}")

                # Tạo liên kết giữa Story và Genre nếu chưa tồn tại
                StoryGenre.objects.get_or_create(story=story, genre=genre)

            self.stdout.write(self.style.SUCCESS("Data imported successfully!"))

        except FileNotFoundError:
            self.stderr.write(f"====[ERROR]====File {json_file} not found!")
        except json.JSONDecodeError as e:
            self.stderr.write(f"====[ERROR]====Error parsing JSON file: {e}")
        except Exception as e:
            self.stderr.write(f"====[ERROR]====Error processing story '{entry.get('Title', 'Unknown')}': {e}")
