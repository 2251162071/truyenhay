from decimal import Decimal
from django.db import models
from unidecode import unidecode
# Create your models here.

class Genre(models.Model):
    name_full = models.CharField(max_length=50, default="noname")  # Tên thể loại có dấu, mặc định là "noname"
    name = models.SlugField(max_length=50, unique=True, blank=True)  # Tên không dấu, URL-friendly
    page_count = models.IntegerField(default=0)  # Số trang, mặc định là 0

    def save(self, *args, **kwargs):
        # Tạo name không dấu từ name_full nếu chưa có
        if not self.name:
            self.name = unidecode(self.name_full).replace(" ", "-").lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name_full

    class Meta:
        managed = False
        db_table = 'app_truyen_genre'

class Story(models.Model):
    chapter_number = models.IntegerField(default=0)  # Thêm field chapter_number để lưu số chương của truyện
    title_full = models.CharField(max_length=255, default="noname")  # Tên truyện có dấu, mặc định là "noname"
    title = models.SlugField(max_length=255, unique=True, blank=True)  # Tên không dấu, URL-friendly

    author = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    views = models.IntegerField()
    updated_at = models.DateTimeField()
    genres = models.ManyToManyField(Genre, through='StoryGenre', related_name='stories')
    rating = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    description = models.TextField(null=True, blank=True)
    image = models.URLField(max_length=500, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.title:  # Chỉ tạo `title` nếu chưa có
            self.title = unidecode(self.title_full).replace(" ", "-").lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title_full

class StoryGenre(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

class Chapter(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=255)
    content = models.TextField()
    chapter_number = models.IntegerField()
    views = models.IntegerField()
    updated_at = models.DateTimeField()

    def __str__(self):
        return f"{self.title} - Chương {self.chapter_number}"

class UserReading(models.Model):
    user_id = models.IntegerField()
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='user_readings')
    last_chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, related_name='+')
    last_read_at = models.DateTimeField()

class HotStory(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    added_at = models.DateTimeField()

class NewUpdatedStory(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    added_at = models.DateTimeField()
