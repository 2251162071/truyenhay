from django.core.management.base import BaseCommand
from app_truyen.models import Story, Genre, StoryGenre

class Command(BaseCommand):
    help = 'Count the number of stories by genre'

    def add_arguments(self, parser):
        parser.add_argument('genre_name', type=str, help='The name of the genre to count stories for')

    def handle(self, *args, **kwargs):
        genre_name = kwargs['genre_name']
        try:
            genre = Genre.objects.get(name=genre_name)
            count = Story.objects.filter(storygenre__genre_id=genre.id).count()
            self.stdout.write(f"Number of stories in genre '{genre_name}': {count}")
        except Genre.DoesNotExist:
            self.stdout.write(f"Genre '{genre_name}' does not exist in the database.")