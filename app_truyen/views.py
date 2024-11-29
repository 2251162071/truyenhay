import asyncio
import logging

from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.http import JsonResponse, HttpResponseRedirect, Http404, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

from app_truyen.models import URLViewCount
from .forms import CommentForm
from .models import Comment
from .models import Story, Chapter
from .services import (
    get_hot_stories,
    get_recommend_stories,
    get_stories_by_genre,
)
from .tasks import crawl_chapters
from .utils import (
    crawl_story,
    save_or_update_story
)
import traceback

logger = logging.getLogger(__name__)

# Trạng thái crawl lưu trong cache
CRAWL_STATUS_KEY = "crawl_status_{story_name}"

def home_view(request):
    danh_sach_truyen_hot = get_hot_stories()
    danh_sach_truyen_de_cu = get_recommend_stories()
    return render(request, 'home/home.html', {'danh_sach_truyen_hot': danh_sach_truyen_hot, 'danh_sach_truyen_de_cu': danh_sach_truyen_de_cu})




def homepage(request):
    views = URLViewCount.objects.all()
    return render(request, 'app_truyen/homepage.html', {'views': views})



def story(request, story_name):
    return get_story_chapters_title(request, story_name, 1)

def story_page_view(request, story_name, page_number):
    return get_story_chapters_title(request, story_name, page_number)

def get_story_chapters_title(request, story_name, page_number):
    start_chapter = (page_number - 1) * 50 + 1
    end_chapter = page_number*50 + 1
    try:
        # Check if the story exists
        story = get_object_or_404(Story, title=story_name)

        # Check the number of chapters in the database
        chapter_count = Chapter.objects.filter(story_id=story.id).count()
        # If the story has no chapters, return an empty list
        if chapter_count == 0:
            # Return an empty list of chapters
            context = {
                'story': story,
                'chapters': [],
                'page_obj': None,
                'has_prev': False,
                'has_next': False,
                'prev_page': None,
                'next_page': None,
                'max_page': 0,
            }
            return render(request, 'app_truyen/truyen.html', context)
        if end_chapter > story.chapter_number:
            end_chapter = chapter_count + 1

        # TODO: Start edit code
        # chapters = Chapter.objects.filter(story_id=story.id).only('id', 'title', 'chapter_number').order_by(
        #     'chapter_number')
        chapters = Chapter.objects.filter(
            story_id=story.id,
            chapter_number__range=(start_chapter, end_chapter)
        ).only('id', 'title', 'chapter_number').order_by('chapter_number')
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
            'has_prev': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'prev_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'max_page': paginator.num_pages,
        }
        return render(request, 'app_truyen/truyen.html', context)
        # TODO: End edit code

        # # If the story has no chapters or the chapter count does not match the story's chapter_number field
        # if chapter_count == 0 or chapter_count < story.chapter_number:
        #
        #     try:
        #         # Crawl missing chapters
        #         # result = asyncio.run(crawl_chapters_async(story_name, start_chapter, end_chapter))
        #         result = crawl_chapters(story_name, start_chapter, end_chapter)
        #     except Exception as e:
        #         logger.error(f"Error calling crawl_chapters_async: {e}")
        #         return JsonResponse({'status': 'error', 'message': 'Error during data crawling.'}, status=500)
        #
        #     # Thuc hien phan trang cho result
        #     paginator = Paginator(result, 50)
        #     page_number = request.GET.get('page', 1)
        #
        #     try:
        #         page_number = int(page_number)
        #     except ValueError:
        #         page_number = 1
        #
        #     page_obj = paginator.get_page(page_number)
        #
        #     context = {
        #         'story': story,
        #         'chapters': page_obj.object_list,
        #         'page_obj': page_obj,
        #         'has_prev': page_obj.has_previous(),
        #         'has_next': page_obj.has_next(),
        #         'prev_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        #         'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        #         'max_page': paginator.num_pages,
        #         'result': result,
        #     }
        #
        #     return render(request, 'app_truyen/truyen.html', context)
        #
        # else:
        #
        #     # If the story has all chapters, return the data
        #     chapters = Chapter.objects.filter(story_id=story.id).only('id', 'title', 'chapter_number').order_by(
        #         'chapter_number')
        #     paginator = Paginator(chapters, 50)
        #     page_number = request.GET.get('page', 1)
        #
        #     try:
        #         page_number = int(page_number)
        #     except ValueError:
        #         page_number = 1
        #
        #     page_obj = paginator.get_page(page_number)
        #
        #     context = {
        #         'story': story,
        #         'chapters': page_obj.object_list,
        #         'page_obj': page_obj,
        #         'has_prev': page_obj.has_previous(),
        #         'has_next': page_obj.has_next(),
        #         'prev_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        #         'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        #         'max_page': paginator.num_pages,
        #     }
        #     return render(request, 'app_truyen/truyen.html', context)

    except DatabaseError as db_error:
        logger.error(f"Lỗi cơ sở dữ liệu: {db_error}")
        print(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': 'Lỗi hệ thống. Vui lòng thử lại sau.'}, status=500)
    except Http404:
        # TODO: Start edit code
        # return 404 page
        return render(request, '404.html', {'error': f"Không tìm thấy truyện '{story_name}'."})
        # TODO: End edit code
        # # Nếu không tồn tại, crawl thông tin truyện
        # crawl_result = crawl_story(f"{settings.CRAWL_URL}/{story_name}")
        # if crawl_result['exists']:
        #     # Lưu thông tin Story vào database
        #     story_info = crawl_result['story_info']
        #     story, created = save_or_update_story(story_info)
        #     # Gọi lại hàm `story_view` bằng cách redirect
        #     return HttpResponseRedirect(reverse('story_detail', args=[story_name]))
        # else:
        #     # Nếu crawl thất bại, trả về 404
        #     return HttpResponseNotFound(f"Unable to crawl story '{story_name}': {crawl_result['error']}")
    except Exception as e:
        logger.error(f"Lỗi không xác định trong story_view: {e}")
        print(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': 'Đã xảy ra lỗi không xác định.'}, status=500)

def crawl_status_view(request, story_name):
    status = cache.get(CRAWL_STATUS_KEY.format(story_name=story_name), False)
    return JsonResponse({'crawling': status})


def chapter_view(request, story_name, chapter_number):
    # chapter_data = get_chapter_data(story_name, chapter_number)
    # if not chapter_data['exists']:
    #     return render(request, '404.html', {'error': chapter_data['error']})

    story = get_object_or_404(Story, title=story_name)
    current_chapter = get_object_or_404(Chapter, story=story, chapter_number=chapter_number)

    # Get previous and next chapters
    previous_chapter = Chapter.objects.filter(story=story, chapter_number__lt=chapter_number).order_by('-chapter_number').first()
    next_chapter = Chapter.objects.filter(story=story, chapter_number__gt=chapter_number).order_by('chapter_number').first()

    context = {
        'story': story_name,
        'story_full':story.title_full,
        'current_chapter': current_chapter,
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
    if not stories:  # Kiểm tra nếu không có truyện
        return render(request, '404.html', {'error': f"Không tìm thấy truyện nào thuộc thể loại '{the_loai}'."})

    stories = stories.order_by('title')

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



# def comment_view(request):
#     if settings.LOGIN_REQUIRED_FOR_COMMENTS and not request.user.is_authenticated:
#         return redirect('login')  # Redirect to login page if login is required and user is not authenticated
#
#     if request.method == 'POST':
#         form = CommentForm(request.POST)
#         if form.is_valid():
#             comment = form.save(commit=False)
#             comment.user = request.user if request.user.is_authenticated else None
#             # Sử dụng URL mặc định nếu không có HTTP_REFERER
#             comment.page_url = request.META.get('HTTP_REFERER', '/comments/')
#             comment.save()
#             return redirect(comment.page_url)
#     else:
#         form = CommentForm()
#
#     # Lấy URL hiện tại hoặc URL mặc định
#     current_url = request.META.get('HTTP_REFERER', '/comments/')
#     comments = Comment.objects.filter(page_url=current_url).order_by('-created_at')
#     return render(request, 'app_truyen/comments.html', {'form': form, 'comments': comments})
