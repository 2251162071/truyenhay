import os
from .models import Story, Chapter, Genre, HotStory
from .utils import get_chapter_content
from django.utils import timezone
import logging
logger = logging.getLogger(__name__)
from dotenv import load_dotenv
load_dotenv()

CRAWL_URL = os.getenv('CRAWL_URL')

if not CRAWL_URL:
    logger.error("CRAWL_URL is not configured in the environment variables.")

def get_hot_stories():
    hot_stories = HotStory.objects.select_related('story').all()
    return [
        {
            'title': hot_story.story.title,
            'title_full': hot_story.story.title_full,
            'author': hot_story.story.author,
            'status': hot_story.story.status,
            'views': hot_story.story.views,
            'description': hot_story.story.description,
            'rating': hot_story.story.rating,
            'image': hot_story.story.image,
            'image_path': 'images/' + hot_story.story.image,
            'link': f'/{hot_story.story.title}/',
        }
        for hot_story in hot_stories
    ]

def get_recommend_stories():
    # Find 5 stories with max views
    recommend_stories = Story.objects.order_by('-views')[:5]
    return [
        {
            'title': story.title,
            'title_full': story.title_full,
            'author': story.author,
            'status': story.status,
            'views': story.views,
            'description': story.description,
            'rating': story.rating,
            'image': story.image,
            'image_path': 'images/' + story.image,
            'link': f'/{story.title}/',
        }
        for story in recommend_stories
    ]

def get_story_data(story_title):
    try:
        story = Story.objects.get(title=story_title)
        return {'exists': True, 'story': story}
    except Story.DoesNotExist:
        return {'exists': False, 'error': 'Story does not exist'}


def get_chapters_by_story_name(story_name, page_number=1):
    chapter_min = (page_number - 1) * 50 + 1
    chapter_max = page_number * 50
    try:
        story = Story.objects.get(title=story_name)
        chapters = Chapter.objects.filter(
            story=story,
            chapter_number__gte=chapter_min,
            chapter_number__lte=chapter_max
        ).only('id', 'title', 'chapter_number')
        return {'chapters': chapters}
    except Story.DoesNotExist:
        return {'error': 'Story does not exist'}


def get_chapter_data(story_name, chapter_number):
    try:
        story = Story.objects.get(title=story_name)
        chapter = Chapter.objects.get(story=story, chapter_number=chapter_number)
        return {
            'exists': True,
            'title': chapter.title,
            'content': chapter.content,
        }
    except (Story.DoesNotExist, Chapter.DoesNotExist):
        return {'exists': False, 'error': 'Chapter does not exist'}


def crawl_chapters_for_story(story_name, page_number):
    try:
        story = Story.objects.get(title=story_name)  # Truy vấn story một lần
        chapter_min = (page_number - 1) * 50 + 1
        chapter_max = page_number * 50

        for chapter_number in range(chapter_min, chapter_max + 1):
            chapter_url = f"{CRAWL_URL}/{story_name}/chuong-{chapter_number}"
            content, title = get_chapter_content(chapter_url)

            if content:
                Chapter.objects.update_or_create(
                    story=story,
                    chapter_number=chapter_number,
                    defaults={
                        'title': title,
                        'content': content,
                        'views':10,
                        'updated_at': timezone.now(),
                    }
                )
    except Story.DoesNotExist:
        logger.error(f"Story {story_name} does not exist")
    except Exception as e:
        logger.error(f"Error while crawling chapters for {story_name}: {str(e)}")


def get_stories_by_genre(genre_name):
    genre = Genre.objects.filter(name=genre_name).first()
    if not genre:
        return None
    return Story.objects.filter(storygenre__genre_id=genre.id).all()


def crawl_chapters(story_title, start_chapter, end_chapter=None):
    try:
        story = Story.objects.get(title=story_title)  # Truy vấn story một lần
        chapters_to_create = []

        # Nếu end_chapter không được cung cấp, chỉ crawl một chương
        if end_chapter is None:
            end_chapter = start_chapter

        if start_chapter <= 0 or (end_chapter and end_chapter < start_chapter):
            raise ValueError("Invalid chapter range")

        for chapter_number in range(start_chapter, end_chapter + 1):
            chapter_url = f"{CRAWL_URL}/{story_title}/chuong-{chapter_number}"
            content, title = get_chapter_content(chapter_url)

            if content:
                chapters_to_create.append(
                    Chapter(
                        story=story,
                        chapter_number=chapter_number,
                        title=title,
                        views=10,
                        content=content,
                        updated_at=timezone.now()
                    )
                )

        # Sử dụng bulk_create nếu crawl nhiều chương
        if len(chapters_to_create) > 1:
            Chapter.objects.bulk_create(chapters_to_create, ignore_conflicts=True)
        elif chapters_to_create:
            chapters_to_create[0].save()  # Lưu chương duy nhất
    except Story.DoesNotExist:
        logger.error(f"Story {story_title} does not exist")
    except ValueError as ve:
        logger.error(str(ve))
    except Exception as e:
        logger.error(f"Error while crawling chapters for {story_title}: {str(e)}")
