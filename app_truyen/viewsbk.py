import os
import re

import requests
from django.http import JsonResponse
from django.shortcuts import render
from .models import Story, HotStory, Chapter, Genre
from django.core.paginator import Paginator
from bs4 import BeautifulSoup
from django.utils import timezone
from dotenv import load_dotenv
load_dotenv()

CRAWL_URL = os.getenv('CRAWL_URL')

def home_view(request):
    hot_stories = HotStory.objects.select_related('story').all()
    danh_sach_truyen_hot = [
        {
            'title': hot_story.story.title,
            'title_full': hot_story.story.title_full,
            'author': hot_story.story.author,
            'status': hot_story.story.status,
            'views': hot_story.story.views,
            'description': hot_story.story.description,
            'rating': hot_story.story.rating,
            'image': hot_story.story.image,
            'image_path': f'images/truyen-tien-hiep/{hot_story.story.title}.webp',
            'chapter_number': hot_story.story.chapter_number,
            'link': f'/{hot_story.story.title}/'
        }
        for hot_story in hot_stories
    ]
    context = {'danh_sach_truyen_hot': danh_sach_truyen_hot}
    return render(request, 'home/home.html', context)

def get_chapter_content(chapter_url):
    response = requests.get(chapter_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    c1 = soup.find('h2')
    c2 = c1.find('a', class_='chapter-title')
    c3 = c2.get_text(strip=True)
    chapter_title = soup.find('h2').find('a', class_='chapter-title').get_text(strip=True)
    chapter_content = soup.find('div', class_='chapter-c')
    # content = chapter_content.get_text(separator='\n', strip=True) if chapter_content else None
    content = chapter_content.decode_contents() if chapter_content else None
    return content, chapter_title

def crawl_chapter_data(chapter_url):
    # Tách tên truyện từ chapter_url dạng 'https://example.com/ten-truyen/chuong-1'
    ten_truyen = chapter_url.split('/')[-2]
    # Tách số chương từ chapter_url dạng 'https://example.com/ten-truyen/chuong-1'
    so_chuong = int(chapter_url.split('/')[-1].split('-')[-1])
    chapter_content, chapter_title = get_chapter_content(chapter_url)
    if not chapter_content is None:
        story = Story.objects.get(title=ten_truyen)
        # Tạo một đối tượng Chapter hoặc cập nhật nếu đã tồn tại
        chapter, created = Chapter.objects.get_or_create(
            story_id=story.id,
            chapter_number=so_chuong,
            defaults={'title': chapter_title, 'content': chapter_content, 'views': 0, 'updated_at': timezone.now()}
        )

        if not created:
            chapter.title = chapter_title
            chapter.content = chapter_content
            chapter.updated_at = timezone.now()
            chapter.save()

def crawl_chapter_of_one_page(story_title, page_number, chapter_total):
    # Lặp từ page_number đến page_number + 50 để crawl dữ liệu từ các trang
    chapter_min = (page_number - 1) * 50 + 1
    chapter_max = page_number * 50
    if chapter_max > chapter_total:
        chapter_max = chapter_total
    for i in range(chapter_min, chapter_max + 1):
        crawl_chapter_data(f'{CRAWL_URL}/{story_title}/chuong-{i}')
def story_view(request, story_name):
    story_data = get_story_data(story_name)
    if not story_data['exists']:
        return render(request, '404.html', {'error': story_data['error']})

    chapter_total = story_data['story']['chapter_number']
    if chapter_total == 0:
        response = get_chapter_total(story_name)
        if 'error' in response:
            return render(request, '404.html', {'error': response['error']})
        chapter_total = response['chapter_total']
    chapters_data = get_chapters_by_story_name(story_name, 1)

    if 'error' in chapters_data:
        return render(request, '404.html', {'error': chapters_data['error']})

    # Handle case where chapters_data is empty
    if not chapters_data['chapters']:
        crawl_chapter_of_one_page(story_name,1, chapter_total)
        # Gọi lại hàm store_view để lấy lại dữ liệu
        chapters_data = get_chapters_by_story_name(story_name, 1)
        if not chapters_data['chapters']:
            return render(request, '404.html', {'error': 'Chapters do not exist'})

    # Paginate and split into 2 columns, each column with up to 25 chapters
    paginator = Paginator(chapters_data['chapters'], 50)  # 50 chapters per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Split into 2 columns
    columns = [page_obj.object_list[i:i + 25] for i in range(0, len(page_obj.object_list), 25)]

    context = {
        'columns': columns,
        'page_obj': page_obj,
        'story_name': story_name,
        'base_url': request.build_absolute_uri('/'),
    }

    return render(request, 'app_truyen/truyen.html', context)

def story_page_view(request, story_name, page_number):
    story_data = get_story_data(story_name)
    if not story_data['exists']:
        return render(request, '404.html', {'error': story_data['error']})

    chapter_total = story_data['story']['chapter_number']
    if chapter_total == 0:
        response = get_chapter_total(story_name)
        if 'error' in response:
            return render(request, '404.html', {'error': response['error']})
        chapter_total = response['chapter_total']
    chapters_data = get_chapters_by_story_name(story_name, page_number)

    if 'error' in chapters_data:
        return render(request, '404.html', {'error': chapters_data['error']})

    # Handle case where chapters_data is empty
    if not chapters_data['chapters']:
        crawl_chapter_of_one_page(story_name,page_number, chapter_total)
        # Gọi lại hàm store_view để lấy lại dữ liệu
        chapters_data = get_chapters_by_story_name(story_name, page_number)
        if not chapters_data['chapters']:
            return render(request, '404.html', {'error': 'Chapters do not exist'})

    # Paginate and split into 2 columns, each column with up to 25 chapters
    paginator = Paginator(chapters_data['chapters'], 50)  # 50 chapters per page
    page_obj = paginator.get_page(page_number)

    # Split into 2 columns
    columns = [page_obj.object_list[i:i + 25] for i in range(0, len(page_obj.object_list), 25)]

    context = {
        'columns': columns,
        'page_obj': page_obj,
        'story_name': story_name,
        'base_url': request.build_absolute_uri('/'),
    }

    return render(request, 'app_truyen/truyen.html', context)
def get_story_data(title):
    """
    Get all data of a story with the given title if it exists in the Story model.

    Args:
        request: The HTTP request object.
        title (str): The title of the story to check.

    Returns:
        JsonResponse: A JSON response with the story data if it exists, otherwise an error message.
    """
    try:
        story = Story.objects.get(title=title)
        story_data = {
            'title': story.title,
            'title_full': story.title_full,
            'author': story.author,
            'status': story.status,
            'views': story.views,
            'description': story.description,
            'rating': story.rating,
            'image': story.image,
            'chapter_number': story.chapter_number,
            'link': f'/{story.title}/'
        }
        return {'exists': True, 'story': story_data}
    except Story.DoesNotExist:
        return {'exists': False, 'error': 'Story does not exist'}

def get_chapter_total(story_name):
    """
    Get the total number of chapters of a story with the given name.

    Args:
        request: The HTTP request object.
        story_name (str): The name of the story.

    Returns:
        JsonResponse: A JSON response with the total number of chapters if the story exists, otherwise an error message.
    """
    try:
        # Gửi request đến URL
        response = requests.get(CRAWL_URL + f'/{story_name}')
        if response.status_code == 404:
            return None
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        #### Lấy thông tin truyện
        # # Lấy tên truyện
        # ten_truyen_full = None
        # if soup.find('h3', class_='title') is not None:
        #     ten_truyen_full = soup.find('h3', class_='title').get_text(strip=True)
        # # Lấy tác giả
        # tac_gia = None
        # if soup.find('a', {'itemprop': 'author'}) is not None:
        #     tac_gia = soup.find('a', {'itemprop': 'author'}).get_text(strip=True)
        # # Lấy thể loại
        # the_loai = 'Tiên Hiệp'
        # # Lấy trạng thái
        # trang_thai = None
        # if soup.find('span', class_='text-primary') is not None:
        #     trang_thai = soup.find('span', class_='text-primary').get_text(strip=True)
        # elif soup.find('span', class_='text-success') is not None:
        #     trang_thai = soup.find('span', class_='text-success').get_text(strip=True)
        # elif soup.find('span', class_='label-hot') is not None:
        #     trang_thai = 'Hot'

        # Lấy số chương
        # Tìm thẻ ul có class pagination
        pagination = soup.find('ul', class_='pagination')
        # Regex để tìm số x trong định dạng "chuong-x"
        pattern = rf'{CRAWL_URL}/{story_name}/chuong-(\d+)'
        numbers = []
        if pagination is not None:
            # Tìm tất cả các thẻ li bên trong ul, rồi lặp qua từng thẻ li để tìm thẻ a có nội dung "Cuối"
            link_cuoi = None
            for li in pagination.find_all('li'):
                a_tag = li.find('a')
                if a_tag and "Cuối" in a_tag.get_text():
                    print("Found the 'Cuối' link:", a_tag['href'])
                    link_cuoi = a_tag['href']
                    break  # Dừng lại nếu đã tìm thấy
            # Gửi request đến link đã tìm được
            response = requests.get(link_cuoi)
            response.raise_for_status()  # Kiểm tra lỗi kết nối

            # Phân tích HTML bằng BeautifulSoup
            so_chuong_soup = BeautifulSoup(response.text, 'html.parser')

            # Duyệt qua từng thẻ <a> và lấy số x
            for link in so_chuong_soup.find_all('a', href=True):
                match = re.search(pattern, link['href'])
                if match:
                    number = int(match.group(1))  # Lấy số x và chuyển thành integer
                    numbers.append(number)
        else:
            for link in soup.find_all('a', href=True):
                match = re.search(pattern, link['href'])
                if match:
                    number = int(match.group(1))  # Lấy số x và chuyển thành integer
                    numbers.append(number)

        # Tìm số lớn nhất
        so_chuong = max(numbers) if numbers else 0
        story = Story.objects.get(title=story_name)
        story.chapter_number = so_chuong
        story.save()
        return {'chapter_total': story.chapter_number}
    except Story.DoesNotExist:
        return {'error': 'Story does not exist'}

def get_chapters_by_story_name(story_name, page_number=1):
    """
    Get all chapters of a story using the story name.

    Args:
        request: The HTTP request object.
        story_name (str): The name of the story.

    Returns:
        JsonResponse: A JSON response with the chapters data.
    """
    chapter_min = (page_number - 1) * 50 + 1
    chapter_max = page_number * 50
    try:
        story = Story.objects.get(title=story_name)
        chapters = Chapter.objects.filter(story_id=story.id, chapter_number__gte=chapter_min, chapter_number__lte=chapter_max).order_by('chapter_number')
        chapters_data = [
            {
                'chapter_title': chapter.title
            }
            for chapter in chapters
        ]
        return {'story_id': story.id, 'chapters': chapters_data}
    except Story.DoesNotExist:
        return {'error': 'Story does not exist'}


def get_chapter_data(story_name, chapter_number):
    """
    Get the data of a chapter with the given number if it exists in the Chapter model.

    Args:
        request: The HTTP request object.
        story_name (str): The name of the story.
        chapter_number (int): The number of the chapter.

    Returns:
        JsonResponse: A JSON response with the chapter data if it exists, otherwise an error message.
    """
    try:
        story = Story.objects.get(title=story_name)
        chapter = Chapter.objects.get(story_id=story.id, chapter_number=chapter_number)
        chapter_html = f"""
                <div class="row mt-4">
                    <div class="col-12 content">
                        <h1 class="text-center">
                            {chapter.title}
                        </h1>
                        {chapter.content}
                    </div>
                </div>
                """
        chapter_data = {
            'title': chapter.title,
            'content': chapter.content,
            'chapter_html': chapter_html,
            'chapter_number': chapter.chapter_number,
            'link': f'/{story.title}/chuong-{chapter.chapter_number}/'
        }
        return {'exists': True, 'chapter': chapter_data}
    except Chapter.DoesNotExist:
        return {'exists': False, 'error': 'Chapter does not exist'}


def chapter_view(request, story_name, chapter_number):
    exists, chapter_data = get_chapter_data(story_name, chapter_number)
    responses = get_chapter_data(story_name, chapter_number)
    if not responses['exists']:
        return render(request, '404.html', {'error': responses['error']})

    context = {
        'story_name': story_name,
        'chapter_number': chapter_number,
        'chapter':  responses['chapter']
    }

    return render(request, 'app_truyen/chuong.html', context)

def get_stories_by_genre(genre_name):
    genre = Genre.objects.filter(name=genre_name).first()
    if not genre:
        return None

    stories = Story.objects.filter(storygenre__genre_id=genre.id).distinct()
    return stories


def genre_view(request, the_loai, so_trang):
    print(f"Đang xem trang {so_trang} của thể loại {the_loai}")
    context = {}

    try:
        so_trang = int(so_trang)
        if so_trang < 1:
            so_trang = 1
    except ValueError:
        so_trang = 1
        context['error_message'] = "Số trang không hợp lệ, tự động chuyển về trang 1."

    stories = get_stories_by_genre(the_loai)
    if not stories:
        return render(request, '404.html', {'error': f"Không tìm thấy truyện nào thuộc thể loại '{the_loai}'."})

    paginator = Paginator(stories, 50)  # 10 stories per page
    page_obj = paginator.get_page(so_trang)

    context.update({
        'danh_sach_truyen': page_obj.object_list,
        'the_loai': the_loai,
        'so_trang': so_trang,
        'has_prev': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'prev_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        'max_page': paginator.num_pages,
        'base_url': request.build_absolute_uri('/'),
    })

    if so_trang > paginator.num_pages:
        context['warning_message'] = f"Trang bạn yêu cầu vượt quá số trang tối đa ({paginator.num_pages})."

    return render(request, 'app_truyen/danh_sach_truyen.html', context)