from django.utils.timezone import now

from truyenhay.settings import CRAWL_URL
from .models import Story
from .utils import fetch_chapter_content, save_or_update_chapter

def crawl_chapters(story_title, start_chapter, end_chapter):
    """
        Crawl chương từ `start_chapter` đến `end_chapter` cho một truyện cụ thể.
        Sử dụng lại hàm `fetch_chapter_content_generic` từ utils.py và `save_or_update_chapter`.
        """
    result = []
    try:
        # Lấy thông tin truyện
        story = Story.objects.get(title=story_title)
    except Story.DoesNotExist:
        print(f"Story '{story_title}' does not exist.")
        return result
    except Exception as e:
        print(f"Error retrieving story '{story_title}': {e}")
        return result

    for chapter_number in range(start_chapter, end_chapter + 1):
        chapter_url = f"{CRAWL_URL}/{story.title}/chuong-{chapter_number}"
        print(f"Fetching content for chapter {chapter_number} of story '{story_title}' from {chapter_url}.")

        # Gọi hàm fetch nội dung chương
        chapter_title, chapter_content = fetch_chapter_content(chapter_url)

        if chapter_title and chapter_content:
            chapter = {
                "chapter_number": chapter_number,
                "story_id": story.id,
                "title": chapter_title,
                "content": chapter_content,
                "views": 10,
                "updated_at": now(),
            }
            # Lưu hoặc cập nhật chương
            try:
                saved_chapter, created = save_or_update_chapter(chapter)
                result.append(saved_chapter)
                print(f"Chapter {chapter_number} of story '{story_title}' saved successfully.")
            except Exception as e:
                print(f"Error saving chapter {chapter_number} of story '{story_title}': {e}")
        else:
            print(
                f"Failed to fetch content for chapter {chapter_number} of story '{story_title}'"
            )

    return result
