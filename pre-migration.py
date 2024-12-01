
import os
import django

# Đặt biến môi trường DJANGO_SETTINGS_MODULE
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "truyenhay.settings")  # Thay 'project_name' bằng tên dự án của bạn

# Khởi tạo Django
django.setup()
from app_truyen.models import StoryGenre, Story, Genre

# Cập nhật StoryGenre để sử dụng title và name
for story_genre in StoryGenre.objects.all():
    story_genre.story_id = Story.objects.get(title=story_genre.story_id).title
    story_genre.genre_id = Genre.objects.get(name=story_genre.genre_id).name
    story_genre.save()

print("Migration completed successfully!")
