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

# logger = logging.getLogger(__name__)

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
    paginator = Paginator(Chapter.objects.filter(story__title=story_name).order_by('chapter_number'), 50)
    page_obj = paginator.get_page(page_number)

    context = {
        'story': get_object_or_404(Story, title=story_name),
        'chapters': page_obj.object_list,
        'page_obj': page_obj,
        'has_prev': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'prev_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        'max_page': paginator.num_pages,
        'base_url': request.build_absolute_uri('/').rstrip('/'),
    }

    return render(request, 'app_truyen/truyen.html', context)

def crawl_status_view(request, story_name):
    status = cache.get(CRAWL_STATUS_KEY.format(story_name=story_name), False)
    return JsonResponse({'crawling': status})


def chapter_view(request, story_name, chapter_number):

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
        'base_url': request.build_absolute_uri('/').rstrip('/'),
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
