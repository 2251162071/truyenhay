from django.core.paginator import Paginator
from django.shortcuts import render
from django.core.cache import cache
from .models import Story, HotStory, Chapter, Genre
from .services import (
    get_hot_stories,
    get_story_data,
    get_chapter_data,
    get_chapters_by_story_name,
    crawl_chapters_for_story,
    get_stories_by_genre,
)

def home_view(request):
    danh_sach_truyen_hot = get_hot_stories()
    return render(request, 'home/home.html', {'danh_sach_truyen_hot': danh_sach_truyen_hot})


def story_view(request, story_name):
    try:
        # Tìm trong cache trước khi truy vấn database
        story_cache_key = f"story_data_{story_name}"
        story = cache.get(story_cache_key)

        if not story:
            story = Story.objects.only('id', 'title', 'chapter_number').get(title=story_name)
            cache.set(story_cache_key, story, timeout=3600)  # Cache trong 1 giờ

        # Cache danh sách chương
        page_number = request.GET.get('page', 1)
        try:
            page_number = int(page_number)
            if page_number < 1:
                page_number = 1
        except ValueError:
            page_number = 1

        chapter_cache_key = f"chapters_{story_name}_page_{page_number}"
        page_obj = cache.get(chapter_cache_key)

        if not page_obj:
            chapters = Chapter.objects.filter(story_id=story.id).only('id', 'title', 'chapter_number')
            paginator = Paginator(chapters, 50)  # 50 chapters per page
            page_obj = paginator.get_page(page_number)
            cache.set(chapter_cache_key, page_obj, timeout=3600)  # Cache trong 1 giờ

        context = {
            'story': story,
            'chapters': page_obj.object_list,
            'page_obj': page_obj,
        }
        return render(request, 'app_truyen/truyen.html', context)
    except Story.DoesNotExist:
        return render(request, '404.html', {'error': 'Story does not exist'})




def chapter_view(request, story_name, chapter_number):
    chapter_data = get_chapter_data(story_name, chapter_number)
    if not chapter_data['exists']:
        return render(request, '404.html', {'error': chapter_data['error']})

    return render(request, 'app_truyen/chuong.html', {'chapter': chapter_data})

def genre_view(request, the_loai, so_trang):
    try:
        so_trang = int(so_trang)
        if so_trang < 1:
            so_trang = 1
    except ValueError:
        so_trang = 1

    stories = get_stories_by_genre(the_loai)
    if not stories:
        return render(request, '404.html', {'error': f"Không tìm thấy truyện nào thuộc thể loại '{the_loai}'."})

    # Phân trang
    paginator = Paginator(stories, 50)  # 50 truyện mỗi trang
    page_obj = paginator.get_page(so_trang)

    # Chuẩn bị danh sách truyện
    danh_sach_truyen = [
        {'title': story.title, 'title_full': story.title_full}
        for story in page_obj.object_list
    ]

    context = {
        'danh_sach_truyen': danh_sach_truyen,
        'the_loai': the_loai,
        'so_trang': so_trang,
        'has_prev': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'prev_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        'max_page': paginator.num_pages,
        'base_url': request.build_absolute_uri('/'),
    }

    return render(request, 'app_truyen/danh_sach_truyen.html', context)
