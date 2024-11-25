# app_truyen/management/commands/insert_genres.py

from django.core.management.base import BaseCommand
from app_truyen.models import Genre

class Command(BaseCommand):
    help = 'Insert sample genres into the Genre model'

    def handle(self, *args, **kwargs):
        sample_genres = [
            {'name': 'tien-hiep', 'name_full': 'Tiên Hiệp', 'page_count': 48},
            {'name': 'xuyen-nhanh', 'name_full': 'Xuyên Nhanh', 'page_count': 14},
            {'name': 'hai-huoc', 'name_full': 'Hài Hước', 'page_count': 72},
            {'name': 'kiem-hiep', 'name_full': 'Kiếm Hiệp', 'page_count': 37},
            {'name': 'trong-sinh', 'name_full': 'Trọng Sinh', 'page_count': 84},
            {'name': 'dien-van', 'name_full': 'Điền Văn', 'page_count': 34},
            {'name': 'ngon-tinh', 'name_full': 'Ngôn Tình', 'page_count': 45},
            {'name': 'trinh-tham', 'name_full': 'Trinh Thám', 'page_count': 45},
            {'name': 'co-dai', 'name_full': 'Cổ Đại', 'page_count': 45},
            {'name': 'dam-my', 'name_full': 'Đam Mỹ', 'page_count': 45},
            {'name': 'tham-hiem', 'name_full': 'Thám Hiểm', 'page_count': 45},
            {'name': 'mat-the', 'name_full': 'Mạt Thế', 'page_count': 45},
            {'name': 'quan-truong', 'name_full': 'Quan Trường', 'page_count': 45},
            {'name': 'linh-di', 'name_full': 'Linh Dị', 'page_count': 45},
            {'name': 'truyen-teen', 'name_full': 'Truyện Teen', 'page_count': 45},
            {'name': 'vong-du', 'name_full': 'Võng Du', 'page_count': 45},
            {'name': 'sac', 'name_full': 'Sắc', 'page_count': 45},
            {'name': 'phuong-tay', 'name_full': 'Phương Tây', 'page_count': 45},
            {'name': 'khoa-huyen', 'name_full': 'Khoa Huyễn', 'page_count': 45},
            {'name': 'nguoc', 'name_full': 'Ngược', 'page_count': 45},
            {'name': 'nu-phu', 'name_full': 'Nữ Phụ', 'page_count': 45},
            {'name': 'he-thong', 'name_full': 'Hệ Thống', 'page_count': 45},
            {'name': 'sung', 'name_full': 'Súng', 'page_count': 45},
            {'name': 'light-novel', 'name_full': 'Light Novel', 'page_count': 45},
            {'name': 'huyen-huyen', 'name_full': 'Huyền Huyễn', 'page_count': 45},
            {'name': 'cung-dau', 'name_full': 'Cung Đấu', 'page_count': 45},
            {'name': 'viet-nam', 'name_full': 'Việt Nam', 'page_count': 45},
            {'name': 'di-gioi', 'name_full': 'Dị Giới', 'page_count': 45},
            {'name': 'nu-cuong', 'name_full': 'Nữ Cường', 'page_count': 45},
            {'name': 'doan-van', 'name_full': 'Đoản Văn', 'page_count': 45},
            {'name': 'di-nang', 'name_full': 'Dị Năng', 'page_count': 45},
            {'name': 'gia-dau', 'name_full': 'Gia Đấu', 'page_count': 45},
            {'name': 'review-sach', 'name_full': 'Review sách', 'page_count': 45},
            {'name': 'quan-su', 'name_full': 'Quân Sự', 'page_count': 45},
            {'name': 'dong-phuong', 'name_full': 'Đông Phương', 'page_count': 45},
            {'name': 'khac', 'name_full': 'Khác', 'page_count': 45},
            {'name': 'lich-su', 'name_full': 'Lịch Sử', 'page_count': 45},
            {'name': 'do-thi', 'name_full': 'Đô Thị', 'page_count': 45},
            {'name': 'xuyen-khong', 'name_full': 'Xuyên Không', 'page_count': 45},
            {'name': 'bach-hop', 'name_full': 'Bách Hợp', 'page_count': 45},
        ]

        for genre_data in sample_genres:
            genre, created = Genre.objects.get_or_create(
                name=genre_data['name'],
                defaults={
                    'name_full': genre_data['name_full'],
                    'page_count': genre_data['page_count']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully inserted genre: {genre_data["name_full"]}'))
            else:
                # Kiểm tra và cập nhật nếu 'page_count' khác
                if genre.page_count != genre_data['page_count']:
                    genre.page_count = genre_data['page_count']
                    genre.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Updated genre: {genre_data["name_full"]} with new page_count'))
                else:
                    self.stdout.write(self.style.WARNING(f'Genre already exists: {genre_data["name_full"]}'))