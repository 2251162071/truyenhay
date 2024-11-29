from django.core.management.base import BaseCommand
from app_truyen.models import Genre

"""
Insert genres into the Genre model
python manage.py insert_genres
"""
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
            {'name': 'ngon-tinh', 'name_full': 'Ngôn Tình', 'page_count': 669},
            {'name': 'trinh-tham', 'name_full': 'Trinh Thám', 'page_count': 26},
            {'name': 'co-dai', 'name_full': 'Cổ Đại', 'page_count': 191},
            {'name': 'dam-my', 'name_full': 'Đam Mỹ', 'page_count': 341},
            {'name': 'tham-hiem', 'name_full': 'Thám Hiểm', 'page_count': 9},
            {'name': 'mat-the', 'name_full': 'Mạt Thế', 'page_count': 14},
            {'name': 'quan-truong', 'name_full': 'Quan Trường', 'page_count': 3},
            {'name': 'linh-di', 'name_full': 'Linh Dị', 'page_count': 32},
            {'name': 'truyen-teen', 'name_full': 'Truyện Teen', 'page_count': 124},
            {'name': 'vong-du', 'name_full': 'Võng Du', 'page_count': 13},
            {'name': 'sac', 'name_full': 'Sắc', 'page_count': 53},
            {'name': 'phuong-tay', 'name_full': 'Phương Tây', 'page_count': 35},
            {'name': 'khoa-huyen', 'name_full': 'Khoa Huyễn', 'page_count': 20},
            {'name': 'nguoc', 'name_full': 'Ngược', 'page_count': 60},
            {'name': 'nu-phu', 'name_full': 'Nữ Phụ', 'page_count': 24},
            {'name': 'he-thong', 'name_full': 'Hệ Thống', 'page_count': 33},
            {'name': 'sung', 'name_full': 'Súng', 'page_count': 158},
            {'name': 'light-novel', 'name_full': 'Light Novel', 'page_count': 2},
            {'name': 'huyen-huyen', 'name_full': 'Huyền Huyễn', 'page_count': 121},
            {'name': 'cung-dau', 'name_full': 'Cung Đấu', 'page_count': 24},
            {'name': 'viet-nam', 'name_full': 'Việt Nam', 'page_count': 0},
            {'name': 'di-gioi', 'name_full': 'Dị Giới', 'page_count': 42},
            {'name': 'nu-cuong', 'name_full': 'Nữ Cường', 'page_count': 69},
            {'name': 'doan-van', 'name_full': 'Đoản Văn', 'page_count': 43},
            {'name': 'di-nang', 'name_full': 'Dị Năng', 'page_count': 26},
            {'name': 'gia-dau', 'name_full': 'Gia Đấu', 'page_count': 14},
            {'name': 'review-sach', 'name_full': 'Review sách', 'page_count': 2},
            {'name': 'quan-su', 'name_full': 'Quân Sự', 'page_count': 8},
            {'name': 'dong-phuong', 'name_full': 'Đông Phương', 'page_count': 6},
            {'name': 'khac', 'name_full': 'Khác', 'page_count': 198},
            {'name': 'lich-su', 'name_full': 'Lịch Sử', 'page_count': 10},
            {'name': 'do-thi', 'name_full': 'Đô Thị', 'page_count': 170},
            {'name': 'xuyen-khong', 'name_full': 'Xuyên Không', 'page_count': 182},
            {'name': 'bach-hop', 'name_full': 'Bách Hợp', 'page_count': 38},
        ]

        for genre_data in sample_genres:
            if genre_data['page_count'] == 0:
                self.stdout.write(self.style.WARNING(f'Skipping genre: {genre_data["name_full"]} (page_count=0)'))
                continue

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
                # Update if 'page_count' is different
                if genre.page_count != genre_data['page_count']:
                    genre.page_count = genre_data['page_count']
                    genre.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Updated genre: {genre_data["name_full"]} with new page_count'))
                else:
                    self.stdout.write(self.style.WARNING(f'Genre already exists: {genre_data["name_full"]}'))
