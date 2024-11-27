from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home_name'),
    path('homepage/', views.homepage, name='homepage'),
    path('<str:story_name>/', views.story_view, name='story_detail'),
    path('crawl-status/<str:story_name>/', views.crawl_status_view, name='crawl_status'),
    # path('<str:story_name>/trang-<int:page_number>/', views.story_page_view, name='story_page_detail'),
    path('<str:story_name>/chuong-<int:chapter_number>/', views.chapter_view, name='chapter_detail'),
    path('the-loai/<str:the_loai>/trang-<int:so_trang>', views.genre_view, name='genre_name'),
    # path('check-status/<str:ten_truyen_str>/chuong-<int:so_chuong_int>/', views.check_story_status_view, name='check_story_status_name'),
    # path('check-status/<str:ten_truyen_str>/', views.check_truyen_status_view, name='check_truyen_status_name'),
    # path('<str:ten_truyen_str>/chuong-<int:so_chuong_int>/', views.chuong_view, name='truyen_chuong_name'),
    path('comments/', views.comment_view, name='comment_view'),
]