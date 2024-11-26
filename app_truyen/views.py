import asyncio

from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import render
from django.core.cache import cache
from django.http import JsonResponse
from .models import Story, HotStory, Chapter, Genre
from django.db import DatabaseError
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from .services import (
    get_hot_stories,
    get_story_data,
    get_chapter_data,
    get_chapters_by_story_name,
    crawl_chapters_for_story,
    get_stories_by_genre,
)
import logging
logger = logging.getLogger(__name__)

from .tasks import crawl_chapters_async

def home_view(request):
    danh_sach_truyen_hot = get_hot_stories()
    return render(request, 'home/home.html', {'danh_sach_truyen_hot': danh_sach_truyen_hot})


# Trạng thái crawl lưu trong cache
CRAWL_STATUS_KEY = "crawl_status_{story_name}"



def story_view(request, story_name):
    try:
        # Sử dụng get_object_or_404 để trả về lỗi 404 nếu không tìm thấy
        story = get_object_or_404(Story.objects.only('id', 'title'), title=story_name)

        # Kiểm tra số lượng chương
        chapter_count = Chapter.objects.filter(story_id=story.id).count()

        if chapter_count == 0:
            # if cache.get(CRAWL_STATUS_KEY.format(story_name=story_name)):
            #     return JsonResponse({'status': 'crawling', 'message': 'Đang tải danh sách chương, vui lòng đợi...'}, status=202)
            #
            # cache.set(CRAWL_STATUS_KEY.format(story_name=story_name), True, timeout=600)

            try:
                asyncio.run(crawl_chapters_async(story_name, 1, 50))
            except Exception as e:
                logger.error(f"Lỗi khi gọi crawl_chapters_async: {e}")
                return JsonResponse({'status': 'error', 'message': 'Lỗi trong quá trình crawl dữ liệu.'}, status=500)

            return JsonResponse({'status': 'crawling', 'message': 'Bắt đầu tải danh sách chương. Trang sẽ tự động làm mới khi hoàn tất.'}, status=202)

        # Nếu đã có chương, trả về dữ liệu
        chapters = Chapter.objects.filter(story_id=story.id).only('id', 'title', 'chapter_number').order_by('chapter_number')
        paginator = Paginator(chapters, 50)
        page_number = request.GET.get('page', 1)

        try:
            page_number = int(page_number)
        except ValueError:
            page_number = 1

        page_obj = paginator.get_page(page_number)

        context = {
            'story': story,
            'chapters': page_obj.object_list,
            'page_obj': page_obj,
        }
        return render(request, 'app_truyen/truyen.html', context)

    except DatabaseError as db_error:
        logger.error(f"Lỗi cơ sở dữ liệu: {db_error}")
        return JsonResponse({'status': 'error', 'message': 'Lỗi hệ thống. Vui lòng thử lại sau.'}, status=500)
    except Exception as e:
        logger.error(f"Lỗi không xác định trong story_view: {e}")
        return JsonResponse({'status': 'error', 'message': 'Đã xảy ra lỗi không xác định.'}, status=500)




def crawl_status_view(request, story_name):
    status = cache.get(CRAWL_STATUS_KEY.format(story_name=story_name), False)
    return JsonResponse({'crawling': status})




def chapter_view(request, story_name, chapter_number):
    chapter_data = get_chapter_data(story_name, chapter_number)
    if not chapter_data['exists']:
        return render(request, '404.html', {'error': chapter_data['error']})

    story = get_object_or_404(Story, title=story_name)
    current_chapter = get_object_or_404(Chapter, story=story, chapter_number=chapter_number)

    # Get previous and next chapters
    previous_chapter = Chapter.objects.filter(story=story, chapter_number__lt=chapter_number).order_by('-chapter_number').first()
    next_chapter = Chapter.objects.filter(story=story, chapter_number__gt=chapter_number).order_by('chapter_number').first()

    context = {
        'story': story_name,
        'chapter': chapter_data,
        'previous_chapter': previous_chapter,
        'next_chapter': next_chapter,
    }

    return render(request, 'app_truyen/chuong.html', context)

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
